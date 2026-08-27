import pandas as pd
import time
from typing import Dict, Any
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

class RealNLtoSQLEngine:
    def __init__(self, api_key: str, db_path: str = "sqlite:///chinook.db"):
        self.api_key = api_key
        self.db = SQLDatabase.from_uri(db_path)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            google_api_key=self.api_key,
            temperature=0
        )
        
        self.prompt = PromptTemplate.from_template(
            "You are a SQLite expert. Given an input question, create a syntactically correct SQLite query to run.\n"
            "Never query for all columns from a specific table, only ask for the relevant columns given the question.\n"
            "DO NOT wrap the SQL in markdown tags (like ```sql). ONLY return the raw SQL query.\n\n"
            "Only use the following tables:\n{table_info}\n\n"
            "Question: {question}\nSQLQuery:"
        )

    def process_query(self, user_query: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            table_info = self.db.get_table_info()
            formatted_prompt = self.prompt.format(table_info=table_info, question=user_query)
            response = self.llm.invoke(formatted_prompt)
            
            # Clean up the markdown if present
            sql_query = response.content.replace("```sql", "").replace("```", "").strip()
            
            engine = create_engine("sqlite:///chinook.db")
            df = pd.read_sql_query(sql_query, engine)
            
            execution_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "success": True,
                "sql_query": sql_query,
                "dataframe": df,
                "execution_time_ms": execution_time,
                "row_count": len(df),
                "dialect": "SQLite",
                "explanation": f"I analyzed the Chinook database schema and used Google Gemini to write this SQL query. It returned {len(df)} rows from the real database."
            }
        except Exception as e:
            return {
                "success": False,
                "sql_query": "-- Failed to generate or execute SQL",
                "dataframe": pd.DataFrame(),
                "execution_time_ms": 0,
                "row_count": 0,
                "dialect": "SQLite",
                "explanation": f"**Error:** Could not process query. Details: {str(e)}"
            }
