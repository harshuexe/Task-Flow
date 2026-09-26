# Ai-Task Flow

Ai-Task Flow is a FastAPI and Next.js task management application with JWT authentication, projects, tasks, team members, file uploads, and dashboard statistics.

## Requirements

- Python 3.12+
- Node.js 20+
- npm

## Local setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn backend.main:app --reload --app-dir ..
```

The API is available at `http://localhost:8000`. Interactive documentation is at `http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

The frontend is available at `http://localhost:3000`.

Register an account at `/register`, then sign in at `/login`.

## Docker

Copy `backend/.env.example` to `backend/.env`, set a strong `SECRET_KEY`, and run:

```powershell
docker compose up --build
```

The frontend runs at `http://localhost:3000` and the API runs at `http://localhost:8000`.

## Main API areas

- `/auth` - registration, login, and profile
- `/projects` - project CRUD
- `/tasks` - task CRUD and status updates
- `/team` - team members
- `/files` - uploads and file records
- `/activity` - activity history
- `/dashboard/stats` - dashboard metrics
.
