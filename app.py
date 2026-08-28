"""
NL-to-SQL Enterprise Streamlit Assistant.

Converts natural language business questions into optimized SQLite queries,
executes them against the live Chinook Database, and renders executive summaries,
automated data visualizations (Bar, Line, Area, Donut, Scatter, KPI metric cards),
syntax-highlighted SQL queries with clause breakdown, and execution diagnostics.

Zero external API keys or live cloud credentials required — operates seamlessly
in both Live Gemini AI Mode and Offline Zero-Credential Demo Mode.
"""

import os
import re
import time
from typing import Dict, Any, List, Optional
import pandas as pd
import streamlit as st

from real_engine import RealNLtoSQLEngine, QueryResult
from chart_engine import AutoVisualizer, ChartSpec
from schema_data import (
    CHINOOK_TABLES,
    SAMPLE_PROMPTS,
    SCHEMA_CATALOG,
    SAMPLE_QUERIES,
    SCHEMA_RELATIONSHIPS,
    get_schema_summary
)


# =============================================================================
# 1. Page Configuration & Enterprise Visual Theme
# =============================================================================

st.set_page_config(
    page_title="NL-to-SQL Enterprise Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS for responsive dark/light mode compatibility and clean typography
st.markdown("""
<style>
    /* Enterprise Typography & Spacing */
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
        line-height: 1.25;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.5rem;
        line-height: 1.5;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 8px;
        background-color: rgba(16, 185, 129, 0.12);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .mode-badge-live {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 8px;
        background-color: rgba(37, 99, 235, 0.12);
        color: #3B82F6;
        border: 1px solid rgba(37, 99, 235, 0.3);
    }
    .mode-badge-offline {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 8px;
        background-color: rgba(245, 158, 11, 0.12);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .metadata-bar {
        font-size: 0.82rem;
        padding: 6px 12px;
        background-color: rgba(148, 163, 184, 0.08);
        border-radius: 8px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        margin-top: 8px;
        margin-bottom: 12px;
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
    }
    .followup-container {
        margin-top: 14px;
        padding-top: 10px;
        border-top: 1px dashed rgba(148, 163, 184, 0.25);
    }
    .welcome-card {
        padding: 20px 24px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.06) 0%, rgba(16, 185, 129, 0.06) 100%);
        border: 1px solid rgba(148, 163, 184, 0.25);
        margin-bottom: 24px;
    }
    .clause-box {
        padding: 8px 12px;
        border-radius: 6px;
        background-color: rgba(148, 163, 184, 0.08);
        border-left: 3px solid #3B82F6;
        margin-bottom: 8px;
        font-size: 0.85rem;
    }
    .clause-title {
        font-weight: 600;
        color: #3B82F6;
        margin-bottom: 3px;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }
    .stCodeBlock {
        margin-top: 6px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. Session State Initialization
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None


# =============================================================================
# 3. Helper Functions
# =============================================================================

def explain_sql_clauses(sql: str) -> Dict[str, str]:
    """
    Extracts and organizes key SQL clauses for breakdown visualization.
    """
    clauses: Dict[str, str] = {}
    if not sql or sql.startswith("--"):
        return clauses

    # Strip inline and block comments
    clean = re.sub(r"--.*$", "", sql, flags=re.MULTILINE).strip()
    clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL).strip()

    patterns = [
        ("SELECT (Projection)", r"\bSELECT\b([\s\S]*?)(?=\bFROM\b|\bWHERE\b|\bGROUP BY\b|\bORDER BY\b|\bLIMIT\b|$)"),
        ("FROM & JOINs (Data Sources)", r"\b(?:FROM|JOIN)\b([\s\S]*?)(?=\bWHERE\b|\bGROUP BY\b|\bHAVING\b|\bORDER BY\b|\bLIMIT\b|$)"),
        ("WHERE (Row Filter)", r"\bWHERE\b([\s\S]*?)(?=\bGROUP BY\b|\bHAVING\b|\bORDER BY\b|\bLIMIT\b|$)"),
        ("GROUP BY (Aggregation Keys)", r"\bGROUP BY\b([\s\S]*?)(?=\bHAVING\b|\bORDER BY\b|\bLIMIT\b|$)"),
        ("HAVING (Group Filter)", r"\bHAVING\b([\s\S]*?)(?=\bORDER BY\b|\bLIMIT\b|$)"),
        ("ORDER BY (Sorting)", r"\bORDER BY\b([\s\S]*?)(?=\bLIMIT\b|$)"),
        ("LIMIT (Result Window)", r"\bLIMIT\b([\s\S]*?)(?=$)"),
    ]

    for clause_name, pat in patterns:
        match = re.search(pat, clean, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if val:
                clauses[clause_name] = val

    return clauses


def render_assistant_turn(msg: Dict[str, Any], msg_idx: int, selected_dialect: str = "SQLite"):
    """
    Renders an Assistant message using the rich 3-Tab container layout:
    - Executive Natural Language Summary
    - Tab 1: Visual Insights & Data (Plotly / Streamlit Chart, Interactive Table, CSV Export)
    - Tab 2: Generated SQL Query (Syntax-highlighted SQL, Clause Breakdown)
    - Tab 3: Diagnostics (Latency, Row Count, Dialect, Model Mode, Error Info)
    - Clickable Follow-up Suggestion Chips
    """
    # 1. Executive Natural Language Explanation
    if msg.get("content"):
        st.markdown(msg["content"])

    df: Optional[pd.DataFrame] = msg.get("df")
    sql_text: str = msg.get("sql", "")
    metrics: Dict[str, Any] = msg.get("metrics", {})
    success: bool = metrics.get("success", True)
    error_type: Optional[str] = metrics.get("error_type")
    exec_time: float = float(metrics.get("execution_time_ms", 0.0))
    row_count: int = int(metrics.get("row_count", len(df) if df is not None else 0))
    dialect_used: str = metrics.get("dialect", selected_dialect)
    is_live: bool = metrics.get("is_live_mode", False)
    followups: List[str] = msg.get("suggested_followups", [])

    # 2. Three-Tab Response Container
    tab_data, tab_sql, tab_diag = st.tabs([
        "📊 Visual Insights & Data",
        "🔍 Generated SQL Query",
        "⚡ Diagnostics"
    ])

    with tab_data:
        if df is not None and not df.empty:
            # Automated Visualization Rendering
            spec = AutoVisualizer.analyze_dataframe(df)
            if spec.is_plottable and spec.chart_type != "none":
                AutoVisualizer.render(df, spec=spec, key_prefix=f"turn_{msg_idx}")
                st.markdown("---")

            # Interactive Tabular Data View
            st.markdown("##### 📋 Interactive Data Table")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Export Data as CSV Button
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv_bytes,
                file_name=f"chinook_query_result_{msg_idx + 1}.csv",
                mime="text/csv",
                key=f"dl_btn_{msg_idx}"
            )

        elif error_type == "empty_result" or (df is not None and df.empty and success):
            st.info("ℹ️ **No Records Found**: No matching records found in the Chinook database for your query criteria.")

        elif error_type == "out_of_scope":
            st.info(
                "❓ **Conversational Guidance**: I am your Chinook Enterprise Data Assistant. "
                "I specialize in music catalog, sales, invoices, and customer analytics. "
                "Please ask questions related to the Chinook database schema."
            )

        elif error_type == "syntax_error":
            st.warning(f"⚠️ **Query Execution Error**: {metrics.get('error_message', 'The generated SQL query could not be executed on the Chinook database.')}")

        elif error_type == "rate_limit":
            st.warning("⏳ **AI Service Rate Limit**: Gemini API quota exceeded. Queries are being served via high-speed Offline Demo Mode.")

        elif error_type == "auth_error":
            st.error("🔑 **Authentication Error**: The provided Google Gemini API key is invalid. Please check your credentials in the sidebar.")

        elif error_type == "security_error":
            st.error("🛡️ **Security Guardrail**: Query blocked because only read-only SELECT queries are permitted on this database.")

        elif not success:
            st.warning(metrics.get("error_message") or "An unexpected issue occurred while executing your query.")

        else:
            st.info("No tabular data returned for this query.")

    with tab_sql:
        if sql_text and not sql_text.startswith("-- Out of scope"):
            st.markdown("##### 📜 Generated SQL Query")
            st.code(sql_text, language="sql")

            # SQL Clause Breakdown
            clauses = explain_sql_clauses(sql_text)
            if clauses:
                with st.expander("🔍 View SQL Clause Breakdown", expanded=False):
                    for clause_name, clause_body in clauses.items():
                        st.markdown(
                            f'<div class="clause-box">'
                            f'<div class="clause-title">{clause_name}</div>'
                            f'<code>{clause_body}</code>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
        elif error_type == "out_of_scope":
            st.caption("No SQL statement generated for non-database inquiries.")
        else:
            st.caption("No SQL statement available.")

    with tab_diag:
        st.markdown("##### ⚡ Query Execution Diagnostics")
        d_col1, d_col2, d_col3, d_col4 = st.columns(4)
        d_col1.metric("Execution Time", f"{exec_time:.1f} ms")
        d_col2.metric("Rows Returned", row_count)
        d_col3.metric("SQL Dialect", dialect_used)
        d_col4.metric("Engine Mode", "🤖 Live Gemini" if is_live else "⚡ Offline Demo")

        diag_details = {
            "status": "Success" if success else f"Error ({error_type or 'general'})",
            "execution_time_ms": exec_time,
            "row_count": row_count,
            "dialect": dialect_used,
            "intent": metrics.get("intent", "data_query"),
            "chart_hint": metrics.get("chart_hint", "auto"),
            "error_type": error_type,
            "error_message": metrics.get("error_message")
        }
        with st.expander("📋 Diagnostic Metadata Payload", expanded=False):
            st.json(diag_details)

    # 3. Clickable Follow-up Suggestion Chips
    if followups:
        st.markdown('<div class="followup-container">', unsafe_allow_html=True)
        st.markdown("💡 **Suggested Follow-up Questions:**")
        cols = st.columns(min(len(followups), 3))
        for f_idx, followup_q in enumerate(followups):
            col = cols[f_idx % len(cols)]
            if col.button(f"🔍 {followup_q}", key=f"chip_{msg_idx}_{f_idx}", use_container_width=True):
                st.session_state.pending_query = followup_q
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# 4. Sidebar Configuration & Schema Explorer
# =============================================================================

# Detect API Key from Secrets or Environment
detected_secret_key = None
try:
    detected_secret_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    pass

detected_env_key = os.environ.get("GEMINI_API_KEY")
default_key = detected_secret_key or detected_env_key or ""

with st.sidebar:
    # Header & Status Badges
    st.markdown('<div class="status-badge">🟢 Connected: Chinook SQLite (11 Tables, 3,503 Tracks)</div>', unsafe_allow_html=True)
    st.title("🤖 NL-to-SQL Assistant")
    st.caption("Enterprise natural language database interface with automated charting and SQL generation.")

    st.markdown("---")

    # API Key Configuration
    st.subheader("🔑 API Key & Engine Mode")
    user_api_key = st.text_input(
        "Google Gemini API Key:",
        type="password",
        value=default_key,
        help="Optional: Paste your Gemini API key for dynamic LLM query generation, or leave blank to use Offline Demo Mode."
    )

    active_api_key = (user_api_key or "").strip()

    # Mode Indicator Badge
    if active_api_key:
        st.markdown('<div class="mode-badge-live">🤖 Live Gemini AI Mode Active</div>', unsafe_allow_html=True)
        st.caption("✨ Dynamic SQL generation enabled via Gemini 1.5 Flash.")
    else:
        st.markdown('<div class="mode-badge-offline">⚡ Offline Demo Mode Active</div>', unsafe_allow_html=True)
        st.caption("⚡ Executing real SQLite benchmark queries without external API dependencies.")

    # Initialize Engine
    engine = RealNLtoSQLEngine(api_key=active_api_key if active_api_key else None)

    st.markdown("---")

    # Dialect Selection
    selected_dialect = st.selectbox(
        "🗄️ SQL Dialect",
        options=["SQLite", "PostgreSQL", "Snowflake", "BigQuery"],
        index=0,
        help="Select target SQL dialect formatting for generated queries."
    )

    st.markdown("---")

    # Categorized Example Queries
    st.subheader("💡 Example Queries")
    st.caption("Click any query below for instant execution:")

    for cat_idx, (cat_name, cat_queries) in enumerate(SAMPLE_PROMPTS.items()):
        with st.expander(f"📂 {cat_name}", expanded=(cat_idx == 0)):
            for q_idx, sample_q in enumerate(cat_queries):
                btn_key = f"btn_sample_{cat_idx}_{q_idx}"
                if st.button(f"👉 {sample_q}", key=btn_key, use_container_width=True):
                    st.session_state.pending_query = sample_q
                    st.rerun()

    st.markdown("---")

    # Dynamic Chinook Database Schema Explorer
    with st.expander("📊 Database Schema Explorer (11 Tables)", expanded=False):
        st.markdown("**Chinook Relational Tables:**")
        for tbl_name, tbl_meta in CHINOOK_TABLES.items():
            st.markdown(f"**📁 `{tbl_name}`** — *{tbl_meta['description']}*")
            st.caption(f"Primary Key: `{tbl_meta['primary_key']}`")
            col_lines = []
            for col in tbl_meta["columns"]:
                pk_indicator = " 🔑 *(PK)*" if col.get("pk") else ""
                col_lines.append(f"- **`{col['name']}`** (`{col['type']}`){pk_indicator}: {col.get('description', '')}")
            st.markdown("\n".join(col_lines))

            if tbl_meta.get("foreign_keys"):
                st.markdown("**Foreign Key Relations:**")
                for fk in tbl_meta["foreign_keys"]:
                    st.markdown(f"- 🔗 `{fk['column']}` ➔ `{fk['references_table']}.{fk['references_column']}`")
            st.markdown("---")

        st.markdown("**Entity Relationships:**")
        for rel in SCHEMA_RELATIONSHIPS:
            st.caption(f"• `{rel['from']}` ➔ `{rel['to']}` ({rel['type']})")

    st.markdown("---")

    # Reset Chat History Action
    if st.button("🗑️ Clear Chat History", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()


# =============================================================================
# 5. Main Application Header
# =============================================================================

st.markdown('<div class="main-header">💬 Enterprise Natural Language to SQL Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'Ask business questions in plain English. The assistant generates optimized SQL queries, '
    'executes them against the live Chinook database, and displays executive summaries, '
    'automated visualizations, and interactive tabular reports.'
    '</div>',
    unsafe_allow_html=True
)


# =============================================================================
# 6. Empty State Welcome Banner
# =============================================================================

if not st.session_state.messages:
    with st.container():
        st.markdown("""
        <div class="welcome-card">
            <h3 style="margin-top:0; font-size:1.3rem;">👋 Welcome to the Chinook NL-to-SQL Assistant!</h3>
            <p style="margin-bottom:12px; color:#64748B;">
                The system connects to the authentic <b>Chinook Relational Database</b> (11 tables, 3,503 tracks).
                Ask any business analytics question or choose a prompt to get started:
            </p>
            <ul style="margin-bottom:12px; color:#475569; line-height:1.7;">
                <li><b>Catalog Analytics:</b> <i>"Who are the top 5 artists by total tracks?"</i></li>
                <li><b>Financial Trends:</b> <i>"What is the total revenue from invoices across all years?"</i></li>
                <li><b>Time Series:</b> <i>"Show annual revenue trend from 2009 to 2013"</i></li>
                <li><b>Customer Intelligence:</b> <i>"Show the top 10 customers by total invoice spend"</i></li>
                <li><b>Staff & Operations:</b> <i>"Show me all employees who are Sales Support Agents"</i></li>
            </ul>
            <p style="font-size:0.85rem; color:#64748B; margin-bottom:0;">
                💡 <i>Tip: The app functions immediately in <b>Offline Demo Mode</b> without API keys, or in <b>Live Gemini AI Mode</b> when an API key is provided.</i>
            </p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# 7. Render Chat History
# =============================================================================

for idx, msg in enumerate(st.session_state.messages):
    role = msg.get("role", "user")
    avatar = "🧑‍💻" if role == "user" else "🤖"

    with st.chat_message(role, avatar=avatar):
        if role == "user":
            st.markdown(msg.get("content", ""))
        else:
            render_assistant_turn(msg, idx, selected_dialect=selected_dialect)


# =============================================================================
# 8. Handle New User Input & Quick Query Execution
# =============================================================================

# Chat input is NEVER disabled, ensuring complete accessibility in Demo and Live modes
user_prompt = st.chat_input("Ask a business question about Chinook music catalog, sales, invoices, or customers...")
query_to_execute = user_prompt or st.session_state.pop("pending_query", None)

if query_to_execute:
    # 1. Append & Render User Message
    st.session_state.messages.append({"role": "user", "content": query_to_execute})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(query_to_execute)

    # 2. Execute Query via Engine
    with st.spinner("Processing natural language query and executing on Chinook database..."):
        result: QueryResult = engine.process_query(query_to_execute, dialect=selected_dialect)

    # 3. Construct Assistant Message Payload
    assistant_msg = {
        "role": "assistant",
        "content": result.explanation,
        "sql": result.sql_query,
        "df": result.dataframe,
        "metrics": {
            "execution_time_ms": result.execution_time_ms,
            "row_count": result.row_count,
            "dialect": result.dialect or selected_dialect,
            "error_type": result.error_type,
            "error_message": result.error_message,
            "success": result.success,
            "chart_hint": result.chart_hint,
            "intent": result.intent or "data_query",
            "is_live_mode": engine.is_live_mode
        },
        "suggested_followups": result.suggested_followups or []
    }

    # 4. Render Assistant Response
    with st.chat_message("assistant", avatar="🤖"):
        render_assistant_turn(assistant_msg, len(st.session_state.messages), selected_dialect=selected_dialect)

    # 5. Append Assistant Message to Session State
    st.session_state.messages.append(assistant_msg)
    st.rerun()
