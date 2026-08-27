"""
Streamlit NL-to-SQL Conversational Assistant Frontend Prototype.
Demonstrates a rich conversational interface for querying relational business data
using natural language, with generated SQL code blocks and native Pandas DataFrames.
Zero external API keys or live database connections required.
"""

import streamlit as st
import pandas as pd
from real_engine import RealNLtoSQLEngine
from schema_data import SCHEMA_CATALOG, SAMPLE_QUERIES, SCHEMA_RELATIONSHIPS

# -----------------------------------------------------------------------------
# 1. Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NL-to-SQL Enterprise Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished enterprise typography and container padding
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: #1E293B;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-demo {
        display: inline-block;
        background-color: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 2px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .metadata-bar {
        font-size: 0.82rem;
        color: #64748B;
        padding: 4px 8px;
        background-color: #F8FAFC;
        border-radius: 6px;
        border: 1px solid #E2E8F0;
        margin-top: 6px;
        margin-bottom: 10px;
    }
    .stCodeBlock {
        margin-top: 8px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Session State Initialization
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "engine" not in st.session_state:
    st.session_state.engine = None

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

engine = st.session_state.engine

# -----------------------------------------------------------------------------
# 3. Sidebar Controls & Schema Explorer
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="badge-demo">?? Real AI Prototype</div>', unsafe_allow_html=True)
    st.title("? NL-to-SQL Assistant")
    st.caption("Convert plain English questions into optimized SQL queries and tabular business data.")
    
    st.markdown("---")
    
    # Check if API key is stored securely in Streamlit Secrets
    secret_key = None
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY")
    except:
        pass
        
    if secret_key:
        st.success("API Key securely loaded from Secrets!")
        st.session_state.engine = RealNLtoSQLEngine(api_key=secret_key)
    else:
        st.subheader("?? API Key")
        api_key = st.text_input("Enter Google Gemini API Key:", type="password", help="Paste your free Gemini API key here")
        if api_key:
            st.session_state.engine = RealNLtoSQLEngine(api_key=api_key)
            st.success("Real AI Engine Activated!")
        else:
            st.warning("Please enter your API key to use the application.")
            st.session_state.engine = None
        


    # Dialect Selection
    selected_dialect = st.selectbox(
        "🗄️ SQL Dialect",
        options=["PostgreSQL", "Snowflake", "BigQuery", "SQLite", "ANSI SQL"],
        index=0,
        help="Select target SQL dialect formatting for generated queries."
    )

    st.markdown("---")

    # Clickable Sample Queries
    st.subheader("💡 Example Queries")
    st.caption("Click any query below to run an instant demonstration:")
    for idx, sample_q in enumerate(SAMPLE_QUERIES):
        if st.button(f"👉 {sample_q}", key=f"btn_sample_{idx}", use_container_width=True):
            st.session_state.pending_query = sample_q
            st.rerun()

    st.markdown("---")

    # Database Schema Explorer
    with st.expander("📊 Database Schema Catalog", expanded=False):
        st.markdown("**Available Tables & Columns:**")
        for table_name, columns in SCHEMA_CATALOG.items():
            st.markdown(f"**`{table_name}`** ({len(columns)} columns)")
            col_list_text = "\n".join([f"  • {col['name']} ({col['type']})" for col in columns])
            st.text(col_list_text)

        st.markdown("**Entity Relationships:**")
        for rel in SCHEMA_RELATIONSHIPS:
            st.caption(f"`{rel['from']}` ➔ `{rel['to']}` ({rel['type']})")

    # Clear Conversation Action
    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()

# -----------------------------------------------------------------------------
# 4. Main Page Header & Banner
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">💬 Enterprise Natural Language to SQL Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'Ask business questions in natural language. The assistant automatically generates SQL queries, '
    'executes them against the live Chinook database, and displays rich interactive tabular reports.'
    '</div>',
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# 5. Empty State Welcome Card
# -----------------------------------------------------------------------------
if not st.session_state.messages:
    welcome_container = st.container()
    with welcome_container:
        st.info("""
        ?? **Welcome to the NL-to-SQL Prototype!**
        
        We are now using the real **Chinook Database** (a digital music store). Try asking questions like:
        - *"Who are the top 5 artists by total tracks?"*
        - *"What is the total revenue from invoices in 2009?"*
        - *"Show me all employees who are Sales Support Agents."*
        
        *Paste your API key in the sidebar to get started!*
        """
        )

for msg in st.session_state.messages:
    avatar_icon = "U" if msg["role"] == "user" else "A"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])
        
        # If assistant response has SQL code
        if msg["role"] == "assistant" and msg.get("sql"):
            with st.expander("🔍 View Generated SQL Query", expanded=False):
                st.code(msg["sql"], language="sql")
                
        # If assistant response has tabular DataFrame
        if msg["role"] == "assistant" and msg.get("df") is not None:
            df_display: pd.DataFrame = msg["df"]
            metrics = msg.get("metrics", {})
            exec_time = metrics.get("execution_time_ms", 18.5)
            row_count = metrics.get("row_count", len(df_display))
            dialect_used = metrics.get("dialect", selected_dialect)

            st.markdown(
                f'<div class="metadata-bar">⚡ <b>Execution Time:</b> {exec_time}ms &nbsp;|&nbsp; '
                f'📋 <b>Rows Returned:</b> {row_count} &nbsp;|&nbsp; '
                f'🗄️ <b>Dialect:</b> {dialect_used}</div>',
                unsafe_allow_html=True
            )
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Export table to CSV
            csv_data = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv_data,
                file_name="query_results.csv",
                mime="text/csv",
                key=f"dl_{id(msg)}"
            )

# -----------------------------------------------------------------------------
# 7. Handle New User Input or Pending Quick Query
# -----------------------------------------------------------------------------
user_prompt = st.chat_input("Ask a business question (e.g., 'What were the top 10 products by revenue in 2025?')...", disabled=st.session_state.engine is None)
query_to_execute = user_prompt or st.session_state.pop("pending_query", None)

if query_to_execute:
    # 1. Record and render User message
    st.session_state.messages.append({"role": "user", "content": query_to_execute})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(query_to_execute)

    # 2. Execute Query via Real LangChain Engine
    result = engine.process_query(query_to_execute)

    # 3. Render Assistant Response
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(result['explanation'])
        
        with st.expander("🔍 View Generated SQL Query", expanded=True):
            st.code(result['sql_query'], language="sql")
            
        st.markdown(
            f'<div class="metadata-bar">⚡ <b>Execution Time:</b> {result['execution_time_ms']}ms &nbsp;|&nbsp; '
            f'📋 <b>Rows Returned:</b> {result['row_count']} &nbsp;|&nbsp; '
            f'🗄️ <b>Dialect:</b> {result.get('dialect', 'SQLite')}</div>',
            unsafe_allow_html=True
        )
        st.dataframe(result['dataframe'], use_container_width=True, hide_index=True)

        # Export CSV Button
        csv_bytes = result['dataframe'].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv_bytes,
            file_name="query_results.csv",
            mime="text/csv",
            key="dl_active_turn"
        )

    # 4. Append Assistant Response to Chat History
    st.session_state.messages.append({
        "role": "assistant",
        "content": result['explanation'],
        "sql": result['sql_query'],
        "df": result['dataframe'],
        "metrics": {
            "execution_time_ms": result['execution_time_ms'],
            "row_count": result['row_count'],
            "dialect": result.get('dialect', 'SQLite'),
            "intent": result.get('intent', 'data_query')
        },
        "suggested_followups": result.get('suggested_followups', [])
    })
