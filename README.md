# Day 3 - AI Sales Lead-to-Reply CRM Agent

Local-first AI CRM workflow in Python + Streamlit using Gemini with human-in-the-loop approval and IST timestamps.

## Features
- Lead intake with phone deduplication (intake.py)
- Gemini draft replies in English / Tanglish / Tamil (gent.py)
- Human approval gate before dry-run send (crm_actions.py)
- Streamlit dashboard & audit log (pp.py)
- JSON persistence & synthetic seed data (storage.py)

## Setup
1. Create a virtual environment and install dependencies:
   pip install -r requirements.txt
2. Copy .env.example or create .env with:
   GEMINI_API_KEY=your_key_here
3. Seed synthetic data and run the dashboard:
   python storage.py
   streamlit run app.py
