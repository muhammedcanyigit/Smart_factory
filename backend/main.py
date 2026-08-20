"""FastAPI uygulama giriş noktası — bkz. docs/decision-log.md Phase 17.

Çalıştırma: uvicorn backend.main:app --reload
Dashboard: http://127.0.0.1:8000/
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router

app = FastAPI(title="Smart Factory Dashboard API")
app.include_router(router, prefix="/api")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
