# To-Do App (Car Theme) - React + FastAPI + PostgreSQL

This repository contains a minimal working scaffold for a To-Do app with:
- Groups
- Invitations (email)
- Task assignment
- Email notifications when invited or assigned

It includes:
- `backend/` - FastAPI app using SQLModel (SQLite/Postgres compatible). Configure DATABASE_URL in backend/.env
- `frontend/` - Vite + React + Tailwind themed to a 'car' UI look

## Quick start
1. Unzip and open in VS Code.
2. Backend: copy `backend/.env.example` to `backend/.env` and fill values (DATABASE_URL, SMTP_*). Then install and run the backend.
3. Frontend: `cd frontend && npm install && npm run dev` (set VITE_API_BASE if backend is not at http://localhost:8000)

Notes:
- Emails require SMTP configured in backend/.env
- The frontend is intentionally simple and focuses on the group/task flow. It uses the API endpoints in the backend.
