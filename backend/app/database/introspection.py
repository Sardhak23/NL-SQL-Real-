"""
backend/app/database/introspection.py
Dynamic SQLite PRAGMA Introspection Engine with In-Memory Schema Cache.
"""

from __future__ import annotations

import time
import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from backend.app.config import settings
from backend.app.database.connection import get_readonly_connection
from backend.app.models.schemas import SchemaResponse, TableInfo, ColumnInfo, ForeignKeyInfo


@dataclass
class ColumnMetadata:
    name: str
    data_type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_nullable: bool = True
    default_value: Optional[Any] = None
    foreign_key_to: Optional[str] = None  # e.g., "categories.category_id"
    sample_values: List[Any] = field(default_factory=list)


@dataclass
class TableMetadata:
    name: str
    row_count: int = 0
    description: Optional[str] = None
    columns: Dict[str, ColumnMetadata] = field(default_factory=dict)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)  # [{"column": "...", "referenced_table": "...", "referenced_column": "..."}]


@dataclass
class SchemaCatalog:
    database_name: str
    db_path: str
    dialect: str = "sqlite"
    total_tables: int = 0
    total_rows: int = 0
    tables: Dict[str, TableMetadata] = field(default_factory=dict)
    relationships: List[Dict[str, str]] = field(default_factory=list)
    graph_adjacency: Dict[str, List[str]] = field(default_factory=dict)
    last_refreshed: float = 0.0


class IntrospectionEngine:
    """Dynamic SQLite Schema Introspector with Thread-Safe Cache."""

    _instance: Optional[IntrospectionEngine] = None
    _lock = threading.Lock()

    def __init__(self, db_path: Optional[Path] = None, ttl_seconds: float = 3600.0):
        self.db_path = db_path or settings.db_path
        self.ttl_seconds = ttl_seconds
        self._cached_catalog: Optional[SchemaCatalog] = None
        self._cache_time: float = 0.0
        self._cache_lock = threading.Lock()

    @classmethod
    def get_instance(cls, db_path: Optional[Path] = None) -> IntrospectionEngine:
        """Singleton accessor."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = IntrospectionEngine(db_path=db_path)
            return cls._instance

    def get_catalog(self, force_refresh: bool = False) -> SchemaCatalog:
        """Retrieve cached schema catalog or introspect database if expired."""
        with self._cache_lock:
            now = time.time()
            if (
                not force_refresh
                and self._cached_catalog is not None
                and (now - self._cache_time) < self.ttl_seconds
            ):
                return self._cached_catalog

            self._cached_catalog = self._introspect_database()
            self._cache_time = now
            return self._cached_catalog

    def refresh(self) -> SchemaCatalog:
        """Force a fresh introspection of the database."""
        return self.get_catalog(force_refresh=True)

    def _introspect_database(self) -> SchemaCatalog:
        """Perform full dynamic SQLite PRAGMA introspection."""
        target_path = Path(self.db_path).resolve()
        if not target_path.exists():
            target_path = settings.refresh_db_path()
            self.db_path = target_path

        catalog = SchemaCatalog(
            database_name=target_path.name,
            db_path=str(target_path),
            dialect="sqlite",
            last_refreshed=time.time(),
        )

        if not target_path.exists():
            return catalog

        try:
            with get_readonly_connection(target_path) as conn:
                cursor = conn.cursor()

                # 1. Discover all user tables
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'android_%' ORDER BY name;"
                )
                table_names = [row[0] for row in cursor.fetchall()]

                total_rows = 0
                graph: Dict[str, List[str]] = {t: [] for t in table_names}
                all_relationships: List[Dict[str, str]] = []

                for tbl in table_names:
                    # Row count
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{tbl}";')
                        r_cnt = cursor.fetchone()[0]
                    except Exception:
                        r_cnt = 0
                    total_rows += r_cnt

                    tbl_meta = TableMetadata(name=tbl, row_count=r_cnt)

                    # 2. Discover columns via PRAGMA table_info
                    cursor.execute(f'PRAGMA table_info("{tbl}");')
                    cols_info = cursor.fetchall()
                    for col_row in cols_info:
                        # col_row: (cid, name, type, notnull, dflt_value, pk)
                        c_name = col_row["name"]
                        c_type = (col_row["type"] or "TEXT").upper()
                        is_pk = bool(col_row["pk"])
                        is_nullable = not bool(col_row["notnull"])
                        dflt = col_row["dflt_value"]

                        if is_pk:
                            tbl_meta.primary_keys.append(c_name)

                        col_meta = ColumnMetadata(
                            name=c_name,
                            data_type=c_type,
                            is_primary_key=is_pk,
                            is_nullable=is_nullable,
                            default_value=dflt,
                        )

                        # Sample distinct values for string/categorical columns
                        if any(t in c_type for t in ("CHAR", "TEXT", "VARCHAR", "STRING")) and not is_pk:
                            try:
                                cursor.execute(
                                    f'SELECT DISTINCT "{c_name}" FROM "{tbl}" WHERE "{c_name}" IS NOT NULL LIMIT 6;'
                                )
                                samples = [r[0] for r in cursor.fetchall() if r[0] is not None]
                                col_meta.sample_values = samples
                            except Exception:
                                col_meta.sample_values = []

                        tbl_meta.columns[c_name] = col_meta

                    # 3. Discover Foreign Keys via PRAGMA foreign_key_list
                    cursor.execute(f'PRAGMA foreign_key_list("{tbl}");')
                    fk_info = cursor.fetchall()
                    for fk_row in fk_info:
                        # fk_row: (id, seq, table, from, to, on_update, on_delete, match)
                        from_col = fk_row["from"]
                        to_table = fk_row["table"]
                        to_col = fk_row["to"]

                        if from_col in tbl_meta.columns:
                            tbl_meta.columns[from_col].is_foreign_key = True
                            tbl_meta.columns[from_col].foreign_key_to = f"{to_table}.{to_col}"

                        fk_entry = {
                            "column": from_col,
                            "referenced_table": to_table,
                            "referenced_column": to_col,
                        }
                        tbl_meta.foreign_keys.append(fk_entry)

                        rel_entry = {
                            "from_table": tbl,
                            "from_column": from_col,
                            "to_table": to_table,
                            "to_column": to_col,
                        }
                        all_relationships.append(rel_entry)

                        # Add undirected edge to adjacency graph
                        if to_table in graph:
                            if to_table not in graph[tbl]:
                                graph[tbl].append(to_table)
                            if tbl not in graph[to_table]:
                                graph[to_table].append(tbl)

                    catalog.tables[tbl] = tbl_meta

                catalog.total_tables = len(table_names)
                catalog.total_rows = total_rows
                catalog.relationships = all_relationships
                catalog.graph_adjacency = graph

        except Exception as e:
            # Degraded graceful fallback
            print(f"[WARN] SQLite Introspection failed on {target_path}: {e}")

        return catalog

    def to_schema_response(self) -> SchemaResponse:
        """Convert introspected catalog to API SchemaResponse."""
        catalog = self.get_catalog()
        tables_list: List[TableInfo] = []

        for tbl_name, tbl_meta in catalog.tables.items():
            cols_list: List[ColumnInfo] = []
            for col_name, col_meta in tbl_meta.columns.items():
                cols_list.append(
                    ColumnInfo(
                        name=col_meta.name,
                        type=col_meta.data_type,
                        is_pk=col_meta.is_primary_key,
                        is_fk=col_meta.is_foreign_key,
                        nullable=col_meta.is_nullable,
                        sample_values=col_meta.sample_values,
                    )
                )

            fks_list: List[ForeignKeyInfo] = [
                ForeignKeyInfo(
                    column=fk["column"],
                    referenced_table=fk["referenced_table"],
                    referenced_column=fk["referenced_column"],
                )
                for fk in tbl_meta.foreign_keys
            ]

            tables_list.append(
                TableInfo(
                    name=tbl_meta.name,
                    row_count=tbl_meta.row_count,
                    description=tbl_meta.description or f"Table containing {tbl_meta.row_count:,} records",
                    columns=cols_list,
                    foreign_keys=fks_list,
                )
            )

        return SchemaResponse(
            database_name=catalog.database_name,
            dialect=catalog.dialect,
            total_tables=catalog.total_tables,
            total_rows=catalog.total_rows,
            tables=tables_list,
        )


def get_introspection_engine() -> IntrospectionEngine:
    """Dependency helper for FastAPI endpoints and engine."""
    return IntrospectionEngine.get_instance()
