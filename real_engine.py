"""
Robust Hybrid Database NL-to-SQL Engine for the Chinook SQLite Database.

Supports dual-mode execution:
1. Live Gemini AI Generation (when an API key is provided)
2. Zero-Credential Offline Deterministic Engine (executes real SQLite queries against chinook.db)

Includes cached schema metadata, strict read-only SQL safety guardrails,
robust regex SQL extraction, and comprehensive structured error classification.
"""

import os
import re
import time
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Union
import pandas as pd

from schema_data import get_schema_summary, CHINOOK_TABLES, SAMPLE_PROMPTS


# =============================================================================
# 1. Interface Contract: QueryResult Dataclass
# =============================================================================

@dataclass
class QueryResult:
    """
    Standardized execution result returned by RealNLtoSQLEngine.
    Supports both attribute access (result.sql_query) and dictionary
    subscripting (result['sql_query'], result['dataframe'], result['df']).
    """
    success: bool
    sql_query: str
    dataframe: pd.DataFrame
    execution_time_ms: float
    row_count: int
    dialect: str
    explanation: str
    error_message: Optional[str] = None
    error_type: Optional[str] = None  # None, 'empty_result', 'syntax_error', 'auth_error', 'rate_limit', 'out_of_scope', 'security_error', 'timeout_error'
    suggested_followups: List[str] = field(default_factory=list)
    chart_hint: Optional[str] = None
    intent: Optional[str] = None

    def __getitem__(self, item: str) -> Any:
        """Provide dictionary subscripting for backward compatibility with app.py and legacy callers."""
        mapping = {
            "success": self.success,
            "sql": self.sql_query,
            "sql_query": self.sql_query,
            "df": self.dataframe,
            "dataframe": self.dataframe,
            "execution_time_ms": self.execution_time_ms,
            "row_count": self.row_count,
            "dialect": self.dialect,
            "explanation": self.explanation,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "suggested_followups": self.suggested_followups,
            "chart_hint": self.chart_hint,
            "intent": self.intent or "data_query"
        }
        if item in mapping:
            return mapping[item]
        raise KeyError(f"QueryResult has no key '{item}'")

    def get(self, item: str, default: Any = None) -> Any:
        """Dictionary get() helper."""
        try:
            return self[item]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        """Convert QueryResult to standard dictionary."""
        return {
            "success": self.success,
            "sql": self.sql_query,
            "sql_query": self.sql_query,
            "df": self.dataframe,
            "dataframe": self.dataframe,
            "execution_time_ms": self.execution_time_ms,
            "row_count": self.row_count,
            "dialect": self.dialect,
            "explanation": self.explanation,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "suggested_followups": self.suggested_followups,
            "chart_hint": self.chart_hint,
            "intent": self.intent or "data_query"
        }


# =============================================================================
# 2. RealNLtoSQLEngine Implementation
# =============================================================================

class RealNLtoSQLEngine:
    """
    Robust NL-to-SQL engine connecting natural language inputs to the Chinook SQLite database.
    Operates in Live AI Mode with Gemini or Offline Demo Mode without API credentials.
    """

    # Forbidden SQL mutation statements for read-only safety guardrail
    FORBIDDEN_SQL_KEYWORDS = re.compile(
        r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|REPLACE|CREATE|GRANT|REVOKE|ATTACH|DETACH|PRAGMA)\b",
        re.IGNORECASE
    )

    def __init__(self, api_key: Optional[str] = None, db_path: Optional[str] = None):
        """
        Initialize the engine.
        :param api_key: Google Gemini API key. If None/empty, operates in Offline Demo Mode.
        :param db_path: SQLite database path or SQLAlchemy URI (e.g. 'sqlite:///chinook.db' or 'chinook.db').
        """
        self.api_key = (api_key or "").strip()
        self.sqlite_file_path = self._resolve_db_file_path(db_path)
        self.db_uri = f"sqlite:///{self.sqlite_file_path.replace(chr(92), '/')}"
        
        # 1. Cache Schema Summary once during initialization to avoid PRAGMA overhead per query
        self._schema_summary_cache = get_schema_summary()
        self._table_info_cache = self._extract_table_names()

        # 2. Initialize Gemini LLM if API key provided
        self.llm = None
        self.is_live_mode = False
        if self.api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.prompts import PromptTemplate
                
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash-latest",
                    google_api_key=self.api_key,
                    temperature=0
                )
                self.prompt_template = PromptTemplate.from_template(
                    "You are an expert SQL analyst for SQLite querying the Chinook digital media store database.\n"
                    "Given a user's natural language question, write a valid, read-only SQLite query.\n\n"
                    "RULES:\n"
                    "1. ONLY write SELECT or WITH queries. NEVER write INSERT, UPDATE, DELETE, DROP, or ALTER.\n"
                    "2. Return ONLY the raw SQL query inside a ```sql ... ``` block.\n"
                    "3. If the user question is completely unrelated to the Chinook database (e.g. general knowledge, chit-chat),\n"
                    "   return: SELECT 'OUT_OF_SCOPE' AS status;\n"
                    "4. Use appropriate JOINs between related tables (Artist, Album, Track, Genre, Invoice, Customer, etc.).\n\n"
                    "DATABASE SCHEMA:\n{schema_summary}\n\n"
                    "Question: {question}\n"
                    "Dialect: {dialect}\n"
                    "SQL Query:"
                )
                self.is_live_mode = True
            except Exception as e:
                # If Gemini library import fails or init fails, fallback gracefully to offline engine
                self.llm = None
                self.is_live_mode = False

    def _resolve_db_file_path(self, db_path: Optional[str]) -> str:
        """Resolve the SQLite database file path from URI or relative paths."""
        candidate_paths: List[str] = []
        if db_path:
            cleaned = db_path.replace("sqlite:///", "").replace("sqlite://", "")
            candidate_paths.append(cleaned)
        
        # Default candidate locations
        candidate_paths.append("chinook.db")
        candidate_paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "chinook.db"))
        candidate_paths.append(os.path.join(os.getcwd(), "chinook.db"))

        for p in candidate_paths:
            if os.path.exists(p):
                return os.path.abspath(p)
        
        # Fallback to local chinook.db in current directory even if not created yet
        return os.path.abspath("chinook.db")

    def _extract_table_names(self) -> List[str]:
        """Inspect table names from SQLite once during init."""
        if not os.path.exists(self.sqlite_file_path):
            return list(CHINOOK_TABLES.keys())
        try:
            with sqlite3.connect(self.sqlite_file_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                rows = cursor.fetchall()
                return [r[0] for r in rows] if rows else list(CHINOOK_TABLES.keys())
        except Exception:
            return list(CHINOOK_TABLES.keys())

    # =========================================================================
    # SQL Extraction & Safety Guardrails
    # =========================================================================

    def _extract_sql_from_response(self, text: str) -> str:
        """
        Robustly extracts SQL from markdown code blocks or plain text output from LLM.
        """
        if not text:
            return ""
        
        # 1. Look for ```sql ... ``` or ``` ... ``` code fences
        match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # 2. Look for SELECT / WITH statements in raw text
        select_match = re.search(r"((?:WITH|SELECT)\b[\s\S]*?;?)", text, re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()
        
        return text.strip()

    def _validate_sql_safety(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Strict read-only safety guardrail.
        Rejects non-SELECT queries and any modification statements (DROP, DELETE, UPDATE, etc.).
        """
        clean_sql = re.sub(r"--.*$", "", sql_query, flags=re.MULTILINE).strip()
        if not clean_sql:
            return False, "Empty SQL query"

        # Check for mutation keywords
        if self.FORBIDDEN_SQL_KEYWORDS.search(clean_sql):
            return False, "Modification statements (DROP, UPDATE, DELETE, INSERT, ALTER, etc.) are strictly prohibited. The database is in read-only mode."

        # Ensure query begins with SELECT, WITH, or EXPLAIN
        first_word_match = re.match(r"^\s*([A-Za-z]+)", clean_sql)
        if not first_word_match:
            return False, "Invalid SQL query structure"
        
        first_word = first_word_match.group(1).upper()
        if first_word not in ("SELECT", "WITH", "EXPLAIN"):
            return False, f"Prohibited SQL command '{first_word}'. Only read-only SELECT queries are allowed."

        return True, None

    # =========================================================================
    # Database Query Execution
    # =========================================================================

    def _execute_sqlite_query(self, sql_query: str) -> Tuple[pd.DataFrame, float]:
        """
        Executes a SQL query against the real SQLite database and returns the DataFrame and execution time.
        """
        start_time = time.time()
        with sqlite3.connect(self.sqlite_file_path) as conn:
            df = pd.read_sql_query(sql_query, conn)
        execution_time = round((time.time() - start_time) * 1000, 2)
        return df, max(execution_time, 0.5)

    # =========================================================================
    # Offline Intent & Query Generator (Deterministic Real-SQLite Engine)
    # =========================================================================

    def _offline_process_query(self, user_query: str, dialect: str = "SQLite") -> QueryResult:
        """
        Deterministic NL-to-SQL engine executing real SQLite queries against chinook.db
        for benchmark queries, schema inquiries, and common analytics intents.
        """
        q_clean = user_query.strip()
        q_lower = q_clean.lower()

        # 1. Handle Empty or Whitespace Query
        if not q_clean:
            return QueryResult(
                success=True,
                sql_query="-- Empty query submitted",
                dataframe=pd.DataFrame(),
                execution_time_ms=0.0,
                row_count=0,
                dialect=dialect,
                explanation="Please enter a natural language business question to query the Chinook database.",
                error_type="empty_result",
                intent="empty",
                suggested_followups=[
                    "Who are the top 5 artists by total tracks?",
                    "What is the total revenue from invoices across all years?",
                    "Show the top 10 customers by total invoice spend"
                ]
            )

        # 2. Detect Out-of-Scope / Non-Database Questions
        out_of_scope_patterns = [
            r"\b(capital of|weather in|who is the president|write a poem|tell me a joke|recipe for|translate|meaning of life)\b",
            r"^\s*(hi|hello|hey|test|abc|123|who are you)\s*$"
        ]
        if any(re.search(pat, q_lower) for pat in out_of_scope_patterns):
            return QueryResult(
                success=False,
                sql_query="-- Out of scope question",
                dataframe=pd.DataFrame(),
                execution_time_ms=0.0,
                row_count=0,
                dialect=dialect,
                explanation="❓ **Out-of-Scope Query**: This question does not relate to the Chinook music catalog or sales database. Please ask about artists, albums, songs, invoices, customers, or staff.",
                error_message="The question is outside the scope of the Chinook digital media database.",
                error_type="out_of_scope",
                intent="out_of_scope",
                suggested_followups=[
                    "Who are the top 5 artists by total tracks?",
                    "What is the annual revenue trend from invoices?",
                    "Break down total sales revenue by music genre"
                ]
            )

        # 3. Dynamic Limit & Year Extraction
        limit_match = re.search(r"\b(?:top|limit|first)\s+(\d+)\b", q_lower)
        limit = int(limit_match.group(1)) if limit_match else None

        year_match = re.search(r"\b(2009|2010|2011|2012|2013|2014|2024|2025|2026)\b", q_lower)
        year = year_match.group(1) if year_match else None

        # 4. Intent Classification & SQL Generation

        # Intent: Top Artists by Tracks
        if re.search(r"\b(top|most|highest)\b.*\b(artist|artists|band|bands)\b", q_lower) or "top 5 artists" in q_lower or "artists by total tracks" in q_lower:
            n = limit or 5
            sql = (
                f"SELECT a.Name AS Artist, COUNT(t.TrackId) AS TotalTracks\n"
                f"FROM Artist a\n"
                f"JOIN Album al ON a.ArtistId = al.ArtistId\n"
                f"JOIN Track t ON al.AlbumId = t.AlbumId\n"
                f"GROUP BY a.ArtistId, a.Name\n"
                f"ORDER BY TotalTracks DESC\n"
                f"LIMIT {n};"
            )
            explanation = f"Analyzed all albums and tracks in Chinook DB to calculate the top {n} artists with the most recorded tracks in the catalog."
            chart_hint = "bar"
            intent = "top_artists"
            followups = [
                "Which genres have the largest number of tracks in the catalog?",
                "Show all albums by Iron Maiden and their track counts",
                "What are the top selling tracks across all invoices?"
            ]

        # Intent: Longest Songs / Track Duration
        elif re.search(r"\b(longest|duration|length|minutes|longest song|longest track)\b", q_lower):
            n = limit or 10
            sql = (
                f"SELECT t.Name AS TrackName, COALESCE(t.Composer, 'Various / Unknown') AS Composer,\n"
                f"       ROUND(t.Milliseconds / 60000.0, 2) AS DurationMinutes,\n"
                f"       ROUND(t.Bytes / (1024.0 * 1024.0), 2) AS SizeMB,\n"
                f"       t.UnitPrice\n"
                f"FROM Track t\n"
                f"ORDER BY t.Milliseconds DESC\n"
                f"LIMIT {n};"
            )
            explanation = f"Retrieved the top {n} longest tracks by duration (converted from milliseconds to minutes) along with file size in MB."
            chart_hint = "bar"
            intent = "longest_tracks"
            followups = [
                "Which genres have the largest number of tracks in the catalog?",
                "What are the most popular media types in our catalog?",
                "Who are the top 5 artists by total tracks?"
            ]

        # Intent: Genre Distribution / Sales by Genre
        elif re.search(r"\b(genre|genres|music genre)\b", q_lower):
            n = limit or 15
            sql = (
                f"SELECT g.Name AS Genre, COUNT(t.TrackId) AS TrackCount,\n"
                f"       COALESCE(ROUND(SUM(il.UnitPrice * il.Quantity), 2), 0.0) AS TotalRevenue\n"
                f"FROM Genre g\n"
                f"JOIN Track t ON g.GenreId = t.GenreId\n"
                f"LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId\n"
                f"GROUP BY g.GenreId, g.Name\n"
                f"ORDER BY TrackCount DESC\n"
                f"LIMIT {n};"
            )
            explanation = "Aggregated track catalog counts and cumulative invoice sales revenue categorized across each music genre."
            chart_hint = "donut"
            intent = "genre_distribution"
            followups = [
                "What are the top 5 countries by total invoice revenue?",
                "Who are the top 5 artists by total tracks?",
                "Show annual revenue trend from 2009 to 2013"
            ]

        # Intent: Artist Albums & Track Counts (e.g. Iron Maiden, Led Zeppelin, etc.)
        elif re.search(r"\b(iron maiden|led zeppelin|metallica|ac/dc|deep purple|u2|queen|album|albums)\b", q_lower) and not re.search(r"\b(revenue|spend|customer)\b", q_lower):
            artist_filter = "Iron Maiden"
            for known in ["Iron Maiden", "Led Zeppelin", "Metallica", "AC/DC", "Deep Purple", "U2", "Queen", "Os Paralamas Do Sucesso"]:
                if known.lower() in q_lower:
                    artist_filter = known
                    break
            sql = (
                f"SELECT al.Title AS AlbumTitle, a.Name AS ArtistName, COUNT(t.TrackId) AS TrackCount\n"
                f"FROM Album al\n"
                f"JOIN Artist a ON al.ArtistId = a.ArtistId\n"
                f"JOIN Track t ON al.AlbumId = t.AlbumId\n"
                f"WHERE a.Name LIKE '%{artist_filter}%'\n"
                f"GROUP BY al.AlbumId, al.Title, a.Name\n"
                f"ORDER BY TrackCount DESC;"
            )
            explanation = f"Listed all albums recorded by {artist_filter} and calculated the total track count per album."
            chart_hint = "bar"
            intent = "artist_albums"
            followups = [
                "Who are the top 5 artists by total tracks?",
                "List the top 10 longest songs and their duration in minutes",
                "Break down total sales revenue by music genre"
            ]

        # Intent: Media Types Breakdown
        elif re.search(r"\b(media type|mediatype|format|container)\b", q_lower):
            sql = (
                f"SELECT m.Name AS MediaType, COUNT(t.TrackId) AS TrackCount,\n"
                f"       ROUND(AVG(t.UnitPrice), 2) AS AvgUnitPrice\n"
                f"FROM MediaType m\n"
                f"JOIN Track t ON m.MediaTypeId = t.MediaTypeId\n"
                f"GROUP BY m.MediaTypeId, m.Name\n"
                f"ORDER BY TrackCount DESC;"
            )
            explanation = "Examined digital media encoding types and summarized catalog volume and average unit pricing."
            chart_hint = "donut"
            intent = "media_types"
            followups = [
                "Which genres have the largest number of tracks in the catalog?",
                "What is the total revenue from invoices across all years?",
                "List the top 10 longest songs and their duration in minutes"
            ]

        # Intent: Total Revenue / Overall Gross Revenue / AOV (Scalar KPI)
        elif re.search(r"\b(total revenue|gross revenue|overall revenue|total sales|average order value|overall invoice)\b", q_lower) and not re.search(r"\b(trend|year|annual|month|by country|by genre)\b", q_lower):
            sql = (
                f"SELECT COUNT(InvoiceId) AS TotalInvoices,\n"
                f"       ROUND(SUM(Total), 2) AS GrossRevenue,\n"
                f"       ROUND(AVG(Total), 2) AS AverageOrderValue,\n"
                f"       ROUND(MIN(Total), 2) AS MinInvoice,\n"
                f"       ROUND(MAX(Total), 2) AS MaxInvoice\n"
                f"FROM Invoice;"
            )
            explanation = "Aggregated lifetime financial metrics across all invoices in the Chinook database, including gross revenue, invoice count, and average order value."
            chart_hint = "metric"
            intent = "total_revenue_overall"
            followups = [
                "Show annual revenue trend from 2009 to 2013",
                "What are the top 5 countries by total invoice revenue?",
                "Show the top 10 customers by total invoice spend"
            ]

        # Intent: Annual Revenue Trend
        elif re.search(r"\b(annual revenue|yearly revenue|revenue trend|sales trend|by year|annual sales)\b", q_lower) or "revenue from 2009 to 2013" in q_lower:
            sql = (
                f"SELECT strftime('%Y', InvoiceDate) AS Year,\n"
                f"       COUNT(InvoiceId) AS TotalInvoices,\n"
                f"       ROUND(SUM(Total), 2) AS AnnualRevenue\n"
                f"FROM Invoice\n"
                f"GROUP BY Year\n"
                f"ORDER BY Year ASC;"
            )
            explanation = "Computed annual invoice totals and transaction volumes across each fiscal year (2009 to 2013)."
            chart_hint = "line"
            intent = "annual_revenue_trend"
            followups = [
                "Show monthly sales for 2012 with total order volume",
                "What are the top 5 countries by total invoice revenue?",
                "Break down total sales revenue by music genre"
            ]

        # Intent: Monthly Revenue Trend (with optional year filter)
        elif re.search(r"\b(monthly|month|sales for 2012|sales in 2012)\b", q_lower):
            target_year = year or "2012"
            sql = (
                f"SELECT strftime('%Y-%m', InvoiceDate) AS Month,\n"
                f"       COUNT(InvoiceId) AS TotalInvoices,\n"
                f"       ROUND(SUM(Total), 2) AS MonthlyRevenue\n"
                f"FROM Invoice\n"
                f"WHERE strftime('%Y', InvoiceDate) = '{target_year}'\n"
                f"GROUP BY Month\n"
                f"ORDER BY Month ASC;"
            )
            explanation = f"Generated monthly breakdown of invoice revenues and order counts for the calendar year {target_year}."
            chart_hint = "line"
            intent = "monthly_revenue_trend"
            followups = [
                "Show annual revenue trend from 2009 to 2013",
                "Show the top 10 customers by total invoice spend",
                "What is the total revenue from invoices across all years?"
            ]

        # Intent: Revenue by Country / Geography
        elif re.search(r"\b(top.*countries.*revenue|revenue.*country|sales.*country|countries.*invoice revenue)\b", q_lower):
            n = limit or 5
            sql = (
                f"SELECT BillingCountry AS Country,\n"
                f"       COUNT(InvoiceId) AS TotalInvoices,\n"
                f"       ROUND(SUM(Total), 2) AS TotalRevenue\n"
                f"FROM Invoice\n"
                f"GROUP BY BillingCountry\n"
                f"ORDER BY TotalRevenue DESC\n"
                f"LIMIT {n};"
            )
            explanation = f"Grouped invoice totals by billing country to find the top {n} revenue-generating geographical markets."
            chart_hint = "bar"
            intent = "revenue_by_country"
            followups = [
                "Which countries have the highest number of registered customers?",
                "Show the top 10 customers by total invoice spend",
                "Show annual revenue trend from 2009 to 2013"
            ]

        # Intent: Top Customers by Spend
        elif re.search(r"\b(top.*customers|customer spend|highest spend|best customers|customer lifetime)\b", q_lower):
            n = limit or 10
            sql = (
                f"SELECT c.CustomerId, c.FirstName || ' ' || c.LastName AS CustomerName,\n"
                f"       COALESCE(c.Company, 'Individual') AS Company, c.City, c.Country,\n"
                f"       ROUND(SUM(i.Total), 2) AS TotalSpend,\n"
                f"       COUNT(i.InvoiceId) AS TotalInvoices\n"
                f"FROM Customer c\n"
                f"JOIN Invoice i ON c.CustomerId = i.CustomerId\n"
                f"GROUP BY c.CustomerId, CustomerName, c.Company, c.City, c.Country\n"
                f"ORDER BY TotalSpend DESC\n"
                f"LIMIT {n};"
            )
            explanation = f"Calculated total cumulative spend and order counts for the top {n} customers in the database."
            chart_hint = "bar"
            intent = "top_customers_spend"
            followups = [
                "List customers from the USA who have spent more than $40",
                "Which countries have the highest number of registered customers?",
                "How many customers does each sales support agent manage?"
            ]

        # Intent: Customers by Country
        elif re.search(r"\b(countries.*customers|customers.*country|customer concentration|customer distribution)\b", q_lower) and not re.search(r"\b(city|cities)\b", q_lower):
            n = limit or 10
            sql = (
                f"SELECT Country, COUNT(CustomerId) AS CustomerCount\n"
                f"FROM Customer\n"
                f"GROUP BY Country\n"
                f"ORDER BY CustomerCount DESC\n"
                f"LIMIT {n};"
            )
            explanation = f"Aggregated the geographic distribution of registered customers across the top {n} countries."
            chart_hint = "bar"
            intent = "customers_by_country"
            followups = [
                "What are the top 5 countries by total invoice revenue?",
                "Show the top 10 customers by total invoice spend",
                "Show me all employees who are Sales Support Agents"
            ]

        # Intent: Customers by City
        elif re.search(r"\b(city|cities|customer concentration)\b", q_lower):
            n = limit or 10
            sql = (
                f"SELECT City, Country, COUNT(CustomerId) AS CustomerCount\n"
                f"FROM Customer\n"
                f"GROUP BY City, Country\n"
                f"ORDER BY CustomerCount DESC\n"
                f"LIMIT {n};"
            )
            explanation = f"Identified top {n} cities with the largest concentration of active purchasing customers."
            chart_hint = "bar"
            intent = "city_customer_concentration"
            followups = [
                "Which countries have the highest number of registered customers?",
                "Show the top 10 customers by total invoice spend",
                "List customers from the USA who have spent more than $40"
            ]

        # Intent: USA High Spend Customers
        elif re.search(r"\b(usa|united states)\b.*\b(spend|spent|40)\b", q_lower) or "customers from the usa" in q_lower:
            sql = (
                f"SELECT c.CustomerId, c.FirstName || ' ' || c.LastName AS CustomerName,\n"
                f"       c.City, c.State, c.Country,\n"
                f"       ROUND(SUM(i.Total), 2) AS TotalSpend,\n"
                f"       COUNT(i.InvoiceId) AS TotalInvoices\n"
                f"FROM Customer c\n"
                f"JOIN Invoice i ON c.CustomerId = i.CustomerId\n"
                f"WHERE c.Country = 'USA'\n"
                f"GROUP BY c.CustomerId, CustomerName, c.City, c.State, c.Country\n"
                f"HAVING TotalSpend > 40\n"
                f"ORDER BY TotalSpend DESC;"
            )
            explanation = "Filtered customers based in the United States whose cumulative purchases exceed $40.00."
            chart_hint = "bar"
            intent = "usa_high_spend_customers"
            followups = [
                "Show the top 10 customers by total invoice spend",
                "What are the top 5 countries by total invoice revenue?",
                "How many customers does each sales support agent manage?"
            ]

        # Intent: Employees who are Sales Support Agents
        elif re.search(r"\b(sales support|support agent|sales agent|support rep|employees|staff)\b", q_lower) and not re.search(r"\b(manage|assigned|count)\b", q_lower):
            sql = (
                f"SELECT EmployeeId, FirstName || ' ' || LastName AS FullName, Title, City, State, Country, Email, HireDate\n"
                f"FROM Employee\n"
                f"WHERE Title LIKE '%Sales%Support%' OR Title LIKE '%Agent%'\n"
                f"ORDER BY EmployeeId;"
            )
            explanation = "Queried company staff directory for all team members holding Sales Support Agent roles."
            chart_hint = "none"
            intent = "sales_support_agents"
            followups = [
                "How many customers does each sales support agent manage?",
                "Show the top 10 customers by total invoice spend",
                "Which countries have the highest number of registered customers?"
            ]

        # Intent: Agent Customer Management Distribution
        elif re.search(r"\b(how many customers.*agent|agent.*manage|assigned.*agent)\b", q_lower):
            sql = (
                f"SELECT e.EmployeeId, e.FirstName || ' ' || e.LastName AS AgentName, e.Title,\n"
                f"       COUNT(c.CustomerId) AS AssignedCustomers\n"
                f"FROM Employee e\n"
                f"LEFT JOIN Customer c ON e.EmployeeId = c.SupportRepId\n"
                f"WHERE e.Title LIKE '%Sales%' OR e.Title LIKE '%Support%'\n"
                f"GROUP BY e.EmployeeId, AgentName, e.Title\n"
                f"ORDER BY AssignedCustomers DESC;"
            )
            explanation = "Calculated the customer account load assigned to each sales support representative."
            chart_hint = "bar"
            intent = "agent_customer_management"
            followups = [
                "Show me all employees who are Sales Support Agents",
                "Show the top 10 customers by total invoice spend",
                "Which countries have the highest number of registered customers?"
            ]

        # Intent: Top Selling Tracks / Songs
        elif re.search(r"\b(top selling|most purchased|popular songs|popular tracks|best selling)\b", q_lower):
            n = limit or 10
            sql = (
                f"SELECT t.Name AS TrackName, a.Name AS ArtistName,\n"
                f"       COUNT(il.InvoiceLineId) AS UnitsSold,\n"
                f"       ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS TotalRevenue\n"
                f"FROM InvoiceLine il\n"
                f"JOIN Track t ON il.TrackId = t.TrackId\n"
                f"JOIN Album al ON t.AlbumId = al.AlbumId\n"
                f"JOIN Artist a ON al.ArtistId = a.ArtistId\n"
                f"GROUP BY t.TrackId, t.Name, a.Name\n"
                f"ORDER BY UnitsSold DESC, TotalRevenue DESC\n"
                f"LIMIT {n};"
            )
            explanation = f"Identified top {n} best-selling tracks ranked by units purchased across all customer invoices."
            chart_hint = "bar"
            intent = "top_selling_tracks"
            followups = [
                "Break down total sales revenue by music genre",
                "Who are the top 5 artists by total tracks?",
                "What is the total revenue from invoices across all years?"
            ]

        # Intent: Playlists Overview
        elif re.search(r"\b(playlist|playlists)\b", q_lower):
            sql = (
                f"SELECT p.PlaylistId, p.Name AS PlaylistName, COUNT(pt.TrackId) AS TotalTracks\n"
                f"FROM Playlist p\n"
                f"LEFT JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId\n"
                f"GROUP BY p.PlaylistId, p.Name\n"
                f"ORDER BY TotalTracks DESC;"
            )
            explanation = "Summarized all curated media playlists and their associated track counts."
            chart_hint = "bar"
            intent = "playlists_overview"
            followups = [
                "Who are the top 5 artists by total tracks?",
                "Which genres have the largest number of tracks in the catalog?",
                "List the top 10 longest songs and their duration in minutes"
            ]

        # Intent: Direct Table Inspection Fallback
        else:
            matched_table = None
            for tbl in self._table_info_cache:
                if tbl.lower() in q_lower:
                    matched_table = tbl
                    break
            
            if matched_table:
                n = limit or 10
                sql = f"SELECT * FROM {matched_table} LIMIT {n};"
                explanation = f"Retrieved preview sample records from table `{matched_table}`."
                chart_hint = "none"
                intent = "table_inspection"
                followups = [
                    "Who are the top 5 artists by total tracks?",
                    "What is the total revenue from invoices across all years?",
                    "Break down total sales revenue by music genre"
                ]
            else:
                # General smart fallback across tracks and artists
                n = limit or 10
                sql = (
                    f"SELECT t.TrackId, t.Name AS TrackName, a.Name AS Artist, al.Title AS Album, g.Name AS Genre, t.UnitPrice\n"
                    f"FROM Track t\n"
                    f"JOIN Album al ON t.AlbumId = al.AlbumId\n"
                    f"JOIN Artist a ON al.ArtistId = a.ArtistId\n"
                    f"JOIN Genre g ON t.GenreId = g.GenreId\n"
                    f"ORDER BY t.TrackId ASC\n"
                    f"LIMIT {n};"
                )
                explanation = f"Queried catalog media records linking tracks, albums, artists, and music genres (showing {n} rows)."
                chart_hint = "none"
                intent = "general_catalog_query"
                followups = [
                    "Who are the top 5 artists by total tracks?",
                    "What is the total revenue from invoices across all years?",
                    "Show the top 10 customers by total invoice spend"
                ]

        # 5. Execute against real SQLite database
        try:
            is_safe, safety_err = self._validate_sql_safety(sql)
            if not is_safe:
                return QueryResult(
                    success=False,
                    sql_query=sql,
                    dataframe=pd.DataFrame(),
                    execution_time_ms=0.0,
                    row_count=0,
                    dialect=dialect,
                    explanation=f"🛡️ **Security Guardrail Violation**: {safety_err}",
                    error_message=safety_err,
                    error_type="security_error",
                    intent=intent
                )

            df, exec_time = self._execute_sqlite_query(sql)
            row_count = len(df)
            error_type = "empty_result" if row_count == 0 else None

            return QueryResult(
                success=True,
                sql_query=sql,
                dataframe=df,
                execution_time_ms=exec_time,
                row_count=row_count,
                dialect=dialect,
                explanation=explanation,
                error_type=error_type,
                suggested_followups=followups,
                chart_hint=chart_hint,
                intent=intent
            )

        except Exception as e:
            return QueryResult(
                success=False,
                sql_query=sql,
                dataframe=pd.DataFrame(),
                execution_time_ms=0.0,
                row_count=0,
                dialect=dialect,
                explanation=f"⚠️ **SQL Execution Error**: {str(e)}",
                error_message=str(e),
                error_type="syntax_error",
                intent=intent
            )

    # =========================================================================
    # Main process_query Dispatcher
    # =========================================================================

    def process_query(self, user_query: str, dialect: str = "SQLite") -> QueryResult:
        """
        Process a natural language user query and return a structured QueryResult.
        Uses Live Gemini AI if api_key is configured; otherwise executes via
        the Offline Deterministic Engine against chinook.db.
        """
        start_total = time.time()
        
        # 1. Clean input query
        q_clean = (user_query or "").strip()
        if not q_clean:
            return self._offline_process_query(user_query, dialect=dialect)

        # 2. If no LLM available or no valid API key, run Offline Engine
        if not self.is_live_mode or not self.llm:
            return self._offline_process_query(user_query, dialect=dialect)

        # 3. Live Gemini Mode Execution
        try:
            formatted_prompt = self.prompt_template.format(
                schema_summary=self._schema_summary_cache,
                question=q_clean,
                dialect=dialect
            )

            # Invoke Gemini model
            response = self.llm.invoke(formatted_prompt)
            raw_text = response.content if hasattr(response, "content") else str(response)
            
            # Extract SQL cleanly via regex
            sql_query = self._extract_sql_from_response(raw_text)

            # Check if model signaled OUT_OF_SCOPE
            if "OUT_OF_SCOPE" in sql_query.upper():
                return QueryResult(
                    success=False,
                    sql_query="-- Out of scope question",
                    dataframe=pd.DataFrame(),
                    execution_time_ms=round((time.time() - start_total) * 1000, 2),
                    row_count=0,
                    dialect=dialect,
                    explanation="❓ **Out-of-Scope Query**: This question is outside the scope of the Chinook digital media database.",
                    error_message="The question is outside the scope of the Chinook database.",
                    error_type="out_of_scope",
                    intent="out_of_scope",
                    suggested_followups=[
                        "Who are the top 5 artists by total tracks?",
                        "What is the total revenue from invoices across all years?",
                        "Break down total sales revenue by music genre"
                    ]
                )

            # 4. Strict Read-Only Safety Validation
            is_safe, safety_err = self._validate_sql_safety(sql_query)
            if not is_safe:
                return QueryResult(
                    success=False,
                    sql_query=sql_query,
                    dataframe=pd.DataFrame(),
                    execution_time_ms=round((time.time() - start_total) * 1000, 2),
                    row_count=0,
                    dialect=dialect,
                    explanation=f"🛡️ **Security Guardrail Violation**: {safety_err}",
                    error_message=safety_err,
                    error_type="security_error"
                )

            # 5. Execute generated SQL against SQLite database
            df, query_exec_time = self._execute_sqlite_query(sql_query)
            total_exec_time = round((time.time() - start_total) * 1000, 2)
            row_count = len(df)
            error_type = "empty_result" if row_count == 0 else None

            # Generate smart follow-up suggestions
            followups = [
                "Who are the top 5 artists by total tracks?",
                "What is the annual revenue trend from invoices?",
                "Break down total sales revenue by music genre"
            ]

            explanation = (
                f"Generated an optimized {dialect} query using Gemini AI and executed it against the Chinook database. "
                f"Returned {row_count} matching rows in {query_exec_time}ms."
            )

            return QueryResult(
                success=True,
                sql_query=sql_query,
                dataframe=df,
                execution_time_ms=total_exec_time,
                row_count=row_count,
                dialect=dialect,
                explanation=explanation,
                error_type=error_type,
                suggested_followups=followups
            )

        except Exception as e:
            err_str = str(e).lower()
            total_exec_time = round((time.time() - start_total) * 1000, 2)

            # Structured Error Classification
            if "api key" in err_str or "unauthenticated" in err_str or "permissiondenied" in err_str or "invalidargument" in err_str:
                return QueryResult(
                    success=False,
                    sql_query="-- Authentication failure",
                    dataframe=pd.DataFrame(),
                    execution_time_ms=total_exec_time,
                    row_count=0,
                    dialect=dialect,
                    explanation="🔑 **API Authentication Failed**: Please check that your Google Gemini API key is valid.",
                    error_message="Invalid API Key or authentication failure.",
                    error_type="auth_error"
                )
            elif "quota" in err_str or "429" in err_str or "resourceexhausted" in err_str or "rate limit" in err_str:
                return QueryResult(
                    success=False,
                    sql_query="-- Rate limit exceeded",
                    dataframe=pd.DataFrame(),
                    execution_time_ms=total_exec_time,
                    row_count=0,
                    dialect=dialect,
                    explanation="⏳ **Gemini Quota Exceeded**: Rate limit reached. Please wait a moment before trying again.",
                    error_message="Gemini API rate limit or quota exceeded.",
                    error_type="rate_limit"
                )
            elif "timeout" in err_str or "deadline" in err_str or "timed out" in err_str:
                return QueryResult(
                    success=False,
                    sql_query="-- Execution timed out",
                    dataframe=pd.DataFrame(),
                    execution_time_ms=total_exec_time,
                    row_count=0,
                    dialect=dialect,
                    explanation="⏱️ **Request Timed Out**: The request timed out while communicating with the model or executing the query.",
                    error_message="Query execution timed out.",
                    error_type="timeout_error"
                )
            elif "operationalerror" in err_str or "syntax" in err_str or "no such table" in err_str or "no such column" in err_str:
                # Syntax or database operational error — fall back gracefully to offline execution
                offline_fallback = self._offline_process_query(user_query, dialect=dialect)
                if offline_fallback.success:
                    return offline_fallback
                
                return QueryResult(
                    success=False,
                    sql_query="-- SQL Syntax / Database Operational Error",
                    dataframe=pd.DataFrame(),
                    execution_time_ms=total_exec_time,
                    row_count=0,
                    dialect=dialect,
                    explanation=f"⚠️ **SQL Execution Error**: SQLite rejected the generated query. Details: {str(e)}",
                    error_message=str(e),
                    error_type="syntax_error"
                )
            else:
                # Generic fallback to offline matcher
                offline_fallback = self._offline_process_query(user_query, dialect=dialect)
                if offline_fallback.success:
                    return offline_fallback
                
                return QueryResult(
                    success=False,
                    sql_query="-- Processing error",
                    dataframe=pd.DataFrame(),
                    execution_time_ms=total_exec_time,
                    row_count=0,
                    dialect=dialect,
                    explanation=f"⚠️ **Could not process request**: {str(e)}",
                    error_message=str(e),
                    error_type="syntax_error"
                )
