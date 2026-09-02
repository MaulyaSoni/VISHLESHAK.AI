"""
Agent API — FastAPI router for data analysis agent
===================================================
Non-blocking execution with job queue and WebSocket updates
"""

import asyncio
import json
import time
import uuid
from typing import Optional
from pathlib import Path

backend_dir = Path(__file__).parent.absolute()
upload_dir = backend_dir / "resources" / "storage" / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Import the agent
try:
    from data_agent_3 import run_agent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    print("[WARN] Data agent not available")

router = APIRouter()

# ─────────────────────────────────────────────
#  JOB MANAGER
# ─────────────────────────────────────────────
class JobManager:
    """Manages async agent jobs with WebSocket broadcast"""
    
    def __init__(self):
        self.jobs = {}
        self.listeners = {}  # job_id -> list of WebSockets
    
    def create_job(self, instruction: str, mode: str = "full") -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'instruction': instruction,
            'mode': mode,
            'steps': [],
            'report': None,
            'error': None,
            'created_at': time.time()
        }
        self.listeners[job_id] = []
        return job_id
    
    def update_job(self, job_id: str, **kwargs):
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)
            self._broadcast(job_id, kwargs)
    
    def get_job(self, job_id: str) -> Optional[dict]:
        return self.jobs.get(job_id)
    
    def list_jobs(self) -> list:
        return list(self.jobs.values())
    
    async def register_ws(self, job_id: str, ws: WebSocket):
        if job_id not in self.listeners:
            self.listeners[job_id] = []
        self.listeners[job_id].append(ws)
    
    def unregister_ws(self, job_id: str, ws: WebSocket):
        if job_id in self.listeners and ws in self.listeners[job_id]:
            self.listeners[job_id].remove(ws)
    
    def _broadcast(self, job_id: str, message: dict):
        """Send update to all WebSocket listeners"""
        if job_id in self.listeners:
            for ws in self.listeners[job_id]:
                try:
                    asyncio.create_task(ws.send_text(json.dumps(message)))
                except:
                    pass

# Global job manager
job_manager = JobManager()

# ─────────────────────────────────────────────
#  REQUEST MODELS
# ─────────────────────────────────────────────
class AgentRunRequest(BaseModel):
    instruction: str = Field(..., min_length=5)
    mode: str = Field("analysis_only", pattern="^(analysis_only|analysis_ml|analysis_ml_notebook|full|eda|ml)$")
    dataset_hash: Optional[str] = None
    step_delay: float = 1.2
    max_steps: int = 18

class AgentStatusResponse(BaseModel):
    job_id: str
    status: str
    steps: list
    report: Optional[dict]
    error: Optional[str]

# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@router.post("/agent/run")
async def run_agent_job(request: AgentRunRequest):
    """Start agent analysis (non-blocking)"""
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent not available")
    
    job_id = job_manager.create_job(request.instruction, request.mode)
    
    # Run in background
    asyncio.create_task(execute_agent_job(job_id, request))
    
    return {
        'job_id': job_id,
        'status': 'started',
        'message': 'Analysis started. Connect to WebSocket for updates.'
    }

@router.get("/agent/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/agent/jobs")
async def list_jobs():
    """List all jobs"""
    return job_manager.list_jobs()

@router.get("/agent/report/{job_id}")
async def get_report(job_id: str):
    """Get final analysis report"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Job not completed")
    return job['report']

@router.websocket("/ws/agent/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket for real-time job updates"""
    job = job_manager.get_job(job_id)
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return
    
    await websocket.accept()
    await job_manager.register_ws(job_id, websocket)
    
    try:
        # Send initial status
        await websocket.send_text(json.dumps({
            'type': 'status',
            'job_id': job_id,
            'status': job['status']
        }))
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        job_manager.unregister_ws(job_id, websocket)

@router.post("/agent/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_manager.update_job(job_id, status='cancelled')
    return {'status': 'cancelled', 'job_id': job_id}

# ─────────────────────────────────────────────
#  FILE UPLOAD
# ─────────────────────────────────────────────

@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload dataset file — returns dataset_hash and preview stats for the frontend."""
    import hashlib
    import pandas as pd

    content = await file.read()

    # Derive a stable hash from file content
    dataset_hash = hashlib.md5(content).hexdigest()

    # Save as <hash>.csv (or keep original extension)
    suffix = Path(file.filename).suffix or ".csv"
    file_path = upload_dir / f"{dataset_hash}{suffix}"
    
    print(f"DEBUG: Uploading file to: {file_path}")
    file_path.write_bytes(content)

    # Parse basic stats
    try:
        df = pd.read_csv(file_path)
        rows, cols = df.shape
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        missing_pct = round(
            df.isnull().sum().sum() / max(1, rows * cols) * 100, 1
        )
        meta = {
            "columns": df.columns.tolist(),
            "numeric_columns": numeric_cols,
            "categorical_columns": cat_cols,
        }
    except Exception:
        rows, cols = 0, 0
        numeric_cols, cat_cols = [], []
        missing_pct = 0.0
        meta = {}

    return {
        "dataset_hash": dataset_hash,
        "filename": file.filename,
        "rows": rows,
        "cols": cols,
        "numeric_count": len(numeric_cols),
        "categorical_count": len(cat_cols),
        "missing_pct": missing_pct,
        "meta": meta,
    }

# ─────────────────────────────────────────────
#  EXECUTION HELPER
# ─────────────────────────────────────────────

async def execute_agent_job(job_id: str, request: AgentRunRequest):
    """Execute agent job in background"""
    try:
        job_manager.update_job(job_id, status='running', progress=10)
        
        # Resolve dataset path from hash
        dataset_path = None
        if request.dataset_hash:
            matching_files = list(upload_dir.glob(f"{request.dataset_hash}.*"))
            if matching_files:
                dataset_path = str(matching_files[0])
                print(f"DEBUG: Agent using dataset: {dataset_path}")

        # Run agent
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: run_agent(
                instruction=request.instruction,
                dataset_path=dataset_path,
                force_task_type=request.mode,
                step_delay=request.step_delay,
                max_steps=request.max_steps
            )
        )
        
        # Update job with results
        job_manager.update_job(
            job_id,
            status='completed',
            report=result,
            progress=100,
            completed_at=time.time()
        )
        
    except Exception as e:
        print(f"ERROR: Agent job {job_id} failed: {str(e)}")
        job_manager.update_job(
            job_id,
            status='failed',
            error=str(e),
            progress=100,
            failed_at=time.time()
        )
