"""Ai-Task Flow API application setup."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models import create_db_and_tables
from routers.auth import router as auth_router
from routers.dashboard import router as dashboard_router
from routers.files import router as files_router
from routers.projects import router as projects_router
from routers.search import router as search_router
from routers.tasks import router as tasks_router

app = FastAPI(title="Ai-Task Flow API", version="1.0.0")
configured_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
)
allowed_origins = [origin.strip().rstrip("/") for origin in configured_origins.split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()

@app.get("/", tags=["Root"])
def root() -> dict:
    return {"name": "Ai-Task Flow API", "status": "ok"}

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(search_router)
app.include_router(tasks_router)
app.include_router(files_router)
app.include_router(dashboard_router)
