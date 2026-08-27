# NL-to-SQL MVP Prototype

This repository contains a frontend prototype for a Natural Language to SQL (NL-to-SQL) conversational agent, built using Streamlit.

## Overview

The application demonstrates how business users can interact with enterprise data using plain English. It simulates the translation of natural language intents into executable SQL queries, rendering both the underlying code and the resulting data tables in a clean, user-friendly chat interface.

### Features
- **Conversational UI**: Built with Streamlit's native chat elements (`st.chat_message`, `st.chat_input`).
- **Mock NL-to-SQL Engine**: Simulates an AI backend capable of intent parsing, parameter extraction, and SQL generation across 7 analytical domains.
- **SQL Inspection**: Users can inspect the generated SQL via collapsible expanders.
- **Data Rendering**: Native tabular rendering for resulting datasets.

## Files
- `app.py`: The main Streamlit application and UI layout.
- `mock_engine.py`: The mock backend translation engine and business logic.
- `schema_data.py`: Relational database catalog and starter questions for the demo.
- `requirements.txt`: Deployment dependencies.

## Deployment
This app is ready to be deployed on [Streamlit Community Cloud](https://share.streamlit.io/). Simply connect this repository and set the main file path to `app.py`.
