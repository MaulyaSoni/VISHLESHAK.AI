"""
Week 3 — FastAPI Backend for Vishleshak AI
===========================================
Production-grade async API with:
  - Non-blocking agent execution
  - WebSocket real-time updates
  - File upload/download
  - Analysis history

Run: uvicorn fastapi_main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Add backend and project root to path so we can import agent and API modules
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "scripts"))
sys.path.insert(0, str(backend_dir / "app_modules"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from agent_api import router as agent_router
from models_api import router as models_router
from auth_api import router as auth_router
from history_api import router as history_router

# New API routers for production features
from api.analysis_api import router as analysis_router
from api.kaggle_api import router as kaggle_router
from api.memory_api import router as memory_router
from api.benchmarks_api import router as benchmarks_router
from api.chat_api import router as chat_router
from api.file_api import router as file_router

# Import new api routers that may have been excluded
from api.analysis_api import router as analysis_quick_router

# ─────────────────────────────────────────────
#  APP LIFECYCLE
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("OK: FastAPI server starting on port 8000")
    print("API Docs: http://localhost:8000/docs")
    yield
    print("FastAPI server shutting down")

# ─────────────────────────────────────────────
#  CREATE APP
# ─────────────────────────────────────────────
app = FastAPI(
    title="Vishleshak AI — Data Analysis Agent",
    description="Production API for automated data analysis",
    version="3.0.0",
    lifespan=lifespan
)

# ─────────────────────────────────────────────
#  MIDDLEWARE (MUST BE ADDED BEFORE ROUTERS)
# ─────────────────────────────────────────────
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000",
                   "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*", "Authorization", "Content-Type",
                   "Accept", "X-Requested-With"],
    expose_headers=["*"],
    max_age=600,
)

# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────
app.include_router(auth_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(file_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(models_router, prefix="/api")

# Production API routes
app.include_router(kaggle_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(benchmarks_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

# ─────────────────────────────────────────────
#  HEALTH CHECK
# ─────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "features": {
            "agent": True,
            "websocket": True,
            "file_upload": True,
            "models": True,
            "analysis": True,
            "kaggle": True,
            "memory": True,
            "benchmarks": True,
            "chat": True
        }
    }

@app.get("/")
def root():
    return {
        "message": "Vishleshak AI API",
        "docs": "/docs",
        "health": "/health"
    }

# ─────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
