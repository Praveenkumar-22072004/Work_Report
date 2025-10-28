# Backend (FastAPI)

1. Copy `backend/.env.example` to `backend/.env` and fill DATABASE_URL and SMTP settings.
2. Create virtualenv and install requirements:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
