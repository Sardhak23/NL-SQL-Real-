"""
backend/app/engine/schema_linker.py
Dynamic Schema Linker: Semantic Entity Linking, Foreign Key Graph Closure, and Context Pruning.
"""

from __future__ import annotations

import re
from typing import List, Set, Dict, Any, Optional, Tuple
from collections import deque

from backend.app.database.introspection import SchemaCatalog, get_introspection_engine


SYNONYM_MAP = {
    "sales": ["orders", "order_items", "total_amount", "total_price"],
    "revenue": ["orders", "order_items", "total_amount", "total_price"],
    "profit": ["products", "order_items", "cost", "price", "total_price"],
    "margin": ["products", "order_items", "cost", "price"],
    "cost": ["products", "order_items", "cost"],
    "spend": ["orders", "customers", "total_amount"],
    "spending": ["orders", "customers", "total_amount"],
    "clv": ["customers", "orders", "total_amount", "loyalty_tier"],
    "lifetime value": ["customers", "orders", "total_amount", "loyalty_tier"],
    "buyer": ["customers"],
    "shopper": ["customers"],
    "client": ["customers"],
    "user": ["customers"],
    "item": ["order_items", "products"],
    "items": ["order_items", "products"],
    "stock": ["inventory", "stock_quantity", "reorder_level"],
    "warehouse": ["inventory", "warehouse_location"],
    "rating": ["reviews", "suppliers", "rating"],
    "feedback": ["reviews"],
    "star": ["reviews", "rating"],
    "stars": ["reviews", "rating"],
    "vendor": ["suppliers"],
    "manufacturer": ["suppliers"],
    "refund": ["orders", "status"],
    "cancellation": ["orders", "status"],
    "cancelled": ["orders", "status"],
    "returned": ["orders", "status"],
    "discount": ["orders", "order_items", "discount_amount", "discount_rate"],
    "tier": ["customers", "loyalty_tier"],
    "loyalty": ["customers", "loyalty_tier"],
    "segment": ["customers", "segment"],
    "signup": ["customers", "signup_date"],
    "signed up": ["customers", "signup_date"],
    "aov": ["orders", "total_amount"],
    "average order value": ["orders", "total_amount"],
}


class SchemaLinker:
    """Extracts entities, resolves foreign key closure, and formats context prompt."""

    def __init__(self, catalog: Optional[SchemaCatalog] = None):
        self.catalog = catalog or get_introspection_engine().get_catalog()

    def link_schema(self, question: str) -> Tuple[List[str], str]:
        """
        Link question to relevant tables and generate compact SQL context string.
        Returns: (matched_table_names, formatted_schema_ddl)
        """
        catalog = self.catalog
        if not catalog or not catalog.tables:
            # Refresh if empty
            catalog = get_introspection_engine().refresh()
            self.catalog = catalog

        if not catalog.tables:
            return [], "-- No tables found in database schema."

        q_lower = question.lower()
        tokens = set(re.findall(r"\b\w+\b", q_lower))

        table_scores: Dict[str, float] = {tbl: 0.0 for tbl in catalog.tables}

        # 1. Check direct table names and singular/plural forms
        for tbl in catalog.tables:
            tbl_lower = tbl.lower()
            if tbl_lower in tokens or tbl_lower in q_lower:
                table_scores[tbl] += 15.0
            # Singular form check
            if tbl_lower.endswith("s") and tbl_lower[:-1] in tokens:
                table_scores[tbl] += 12.0
            if tbl_lower.endswith("ies") and (tbl_lower[:-3] + "y") in tokens:
                table_scores[tbl] += 12.0

        # 2. Check column names and sample values
        for tbl_name, tbl_meta in catalog.tables.items():
            for col_name, col_meta in tbl_meta.columns.items():
                c_lower = col_name.lower()
                if c_lower in tokens or c_lower in q_lower:
                    table_scores[tbl_name] += 8.0

                # Sample value matching
                for sample in col_meta.sample_values:
                    if sample and str(sample).lower() in q_lower:
                        table_scores[tbl_name] += 10.0

        # 3. Check domain synonyms
        for phrase, targets in SYNONYM_MAP.items():
            if phrase in q_lower:
                for target in targets:
                    if target in catalog.tables:
                        table_scores[target] += 6.0
                    else:
                        # Might be a column name
                        for tbl_name, tbl_meta in catalog.tables.items():
                            if target in tbl_meta.columns:
                                table_scores[tbl_name] += 4.0

        # Select tables with score > 0
        scored_tables = [tbl for tbl, sc in table_scores.items() if sc > 0.0]

        # If none matched, or only 1 matched for complex query, fallback to all tables (or top core tables)
        if len(scored_tables) == 0:
            scored_tables = list(catalog.tables.keys())

        # 4. Resolve Foreign Key Relational Graph Closure
        closed_tables = self._resolve_graph_closure(scored_tables, catalog)

        # 5. Format compact schema context DDL
        formatted_ddl = self._format_schema_ddl(closed_tables, catalog)

        return closed_tables, formatted_ddl

    def _resolve_graph_closure(self, selected_tables: List[str], catalog: SchemaCatalog) -> List[str]:
        """Find bridge tables along shortest paths between all pairs of selected tables."""
        if len(selected_tables) <= 1:
            return selected_tables

        result_set: Set[str] = set(selected_tables)
        adjacency = catalog.graph_adjacency

        # Helper BFS to find shortest path between two tables
        def shortest_path(src: str, dst: str) -> List[str]:
            if src == dst:
                return [src]
            visited = {src}
            queue = deque([[src]])
            while queue:
                path = queue.popleft()
                node = path[-1]
                for neighbor in adjacency.get(node, []):
                    if neighbor == dst:
                        return path + [neighbor]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(path + [neighbor])
            return []

        # Connect all pairs
        table_list = list(selected_tables)
        for i in range(len(table_list)):
            for j in range(i + 1, len(table_list)):
                t1, t2 = table_list[i], table_list[j]
                path = shortest_path(t1, t2)
                if path:
                    for node in path:
                        result_set.add(node)

        # Preserve canonical order
        return [tbl for tbl in catalog.tables if tbl in result_set]

    def _format_schema_ddl(self, tables: List[str], catalog: SchemaCatalog) -> str:
        """Render minimal, token-efficient SQL DDL with sample values and FK comments."""
        ddl_parts = []

        for tbl_name in tables:
            if tbl_name not in catalog.tables:
                continue
            tbl_meta = catalog.tables[tbl_name]
            cols_str_list = []

            for col_name, col_meta in tbl_meta.columns.items():
                col_def = f"    {col_name} {col_meta.data_type}"
                if col_meta.is_primary_key:
                    col_def += " PRIMARY KEY"
                if not col_meta.is_nullable:
                    col_def += " NOT NULL"
                if col_meta.foreign_key_to:
                    col_def += f" REFERENCES {col_meta.foreign_key_to}"

                # Append sample values as comment if available
                if col_meta.sample_values and len(col_meta.sample_values) > 0:
                    samples_repr = ", ".join(repr(s) for s in col_meta.sample_values[:4])
                    col_def += f" -- samples: [{samples_repr}]"

                cols_str_list.append(col_def)

            table_ddl = f"-- Table: {tbl_name} ({tbl_meta.row_count:,} records)\nCREATE TABLE {tbl_name} (\n"
            table_ddl += ",\n".join(cols_str_list)
            table_ddl += "\n);"
            ddl_parts.append(table_ddl)

        # Add relationships summary
        rel_comments = []
        for rel in catalog.relationships:
            if rel["from_table"] in tables and rel["to_table"] in tables:
                rel_comments.append(
                    f"-- {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}"
                )

        final_context = "\n\n".join(ddl_parts)
        if rel_comments:
            final_context += "\n\n-- Foreign Key Relationships:\n" + "\n".join(rel_comments)

        return final_context
