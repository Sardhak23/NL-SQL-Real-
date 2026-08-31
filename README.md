<div align="center">
  
# ?? NL-SQL Analytics Copilot (Enterprise Edition)

[![Frontend](https://img.shields.io/badge/Frontend-React_18_%7C_Vite_%7C_TypeScript-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI_%7C_Python_3-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Database-SQLite_(500k+_Rows)-003B57?style=for-the-badge&logo=sqlite)](https://sqlite.org/)
[![AI](https://img.shields.io/badge/AI_Engine-Google_Gemini-4285F4?style=for-the-badge&logo=google)](https://ai.google.dev/)
[![Deployment](https://img.shields.io/badge/Deployment-Vercel_%7C_Render-black?style=for-the-badge&logo=vercel)](https://nl-sql-real.vercel.app)

**A fully decoupled, agentic Natural Language to SQL analytics platform.**

[**?? LIVE DEMO**](https://nl-sql-real.vercel.app) • [**Architecture Specs**](#-system-architecture) • [**Local Setup**](#-local-development)

</div>

---

## ?? Executive Summary

The **NL-SQL Analytics Copilot** is a production-grade SaaS application that translates conversational business questions into highly optimized, dialect-specific SQL queries. 

Originally conceived as a monolithic Streamlit script, the architecture has been completely rewritten into a scalable **React + FastAPI decoupled microservices stack**. It executes against a massive, dynamically generated synthetic e-commerce database containing over **500,000+ orders** and 1.4 million items to prove enterprise scalability.

---

## ? Key Enterprise Features

- **?? Agentic Self-Correction Loop:** If the LLM generates an invalid SQL query or hallucinates a column, the FastAPI backend intercepts the SQLite database error, feeds the stack trace back to the AI, and autonomously corrects the query in the background.
- **??? AST Safety Validator:** A strict 4-stage Abstract Syntax Tree validator strictly blocks all 17 mutating SQL commands (e.g., DROP, DELETE, UPDATE) and stacked injections before execution.
- **?? Dynamic Schema Introspection:** The system does not rely on hardcoded prompts. It dynamically introspects the database at boot, caches relationships (PK/FK), and uses a shortest-path schema linker to only feed the AI relevant tables.
- **?? Auto-Rendering UI:** The React frontend automatically parses the returning JSON payloads and intelligently selects the best Recharts visualization (Bar, Line, Donut, Scatter) while rendering raw data in paginated TanStack tables.

---

## ??? System Architecture

### 1. Frontend (The "Face")
- **Tech Stack:** React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui.
- **Hosting:** Vercel Global Edge Network.
- **Features:** Dark mode SaaS UI, collapsible Schema Explorer, multi-line Query Composer, and a 6-stage Execution Stepper to expose the AI's "thought process."

### 2. Backend (The "Brain")
- **Tech Stack:** FastAPI, Python 3.10+, SQLAlchemy, Pydantic.
- **Hosting:** Render.com.
- **Features:** Asynchronous REST endpoints, dynamic prompt construction, LLM provider abstraction, and strict query validation.

---

## ?? Local Development

To run this application on your local machine, follow these steps:

### Prerequisites
- Node.js (v18+)
- Python (3.10+)

### 1. Start the FastAPI Backend
`ash
# Install dependencies
pip install -r backend/requirements.txt

# Start the server (runs on http://localhost:8000)
uvicorn main:app --reload
`
*(Note: Ensure you have a GEMINI_API_KEY set in your environment variables for live AI generation).*

### 2. Start the React Frontend
`ash
cd frontend

# Install dependencies
npm install

# Start the Vite development server (runs on http://localhost:5173)
npm run dev
`

---
*Built with ?? for the next generation of conversational analytics.*
