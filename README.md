# Day 3 - AI Sales Lead-to-Reply CRM Agent

Local-first AI CRM workflow in Python + Streamlit using Gemini with human-in-the-loop approval and IST timestamps.

## Features
- Lead intake with phone deduplication (`intake.py`)
- Gemini draft replies in English / Tanglish / Tamil (`agent.py`)
- Human approval gate before dry-run send (`crm_actions.py`)
- Streamlit dashboard & audit log (`app.py`)
- JSON persistence & synthetic seed data (`storage.py`)

## Setup
1. Install dependencies: pip install -r requirements.txt
2. Create .env with: GEMINI_API_KEY=your_key_here
3. Seed data and run: python storage.py &&amp; streamlit run app.py
