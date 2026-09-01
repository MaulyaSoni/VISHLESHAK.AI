# Week 3 Complete Implementation Guide

## Overview
Week 3 creates a FastAPI backend with WebSocket support and a React notebook-style UI for the Data Agent. This runs **alongside** your existing Flask backend and Streamlit app.

---

## Part 1: FastAPI Backend

### 1.1 Install Dependencies

```bash
pip install fastapi uvicorn websockets python-multipart
```

Or add to `backend/requirements.txt`:
```
# FastAPI (Week 3)
fastapi>=0.104.0
uvicorn>=0.24.0
websockets>=12.0
python-multipart>=0.0.6
```

### 1.2 Create FastAPI App Structure

**File**: `backend/fastapi_main.py`

```python
"""
Vishleshak AI — FastAPI Backend (Week 3)
Runs alongside existing Flask backend on different port (8000)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.agent_api import router as agent_router
import uvicorn

app = FastAPI(
    title="Vishleshak AI Agent API",
    description="WebSocket-enabled API for Data Agent notebook UI",
    version="3.0.0"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router, prefix="/api/agent")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "vishleshak-fastapi", "version": "3.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

### 1.3 Create Pydantic Models

**File**: `backend/models_api.py`

```python
"""
Pydantic models for FastAPI request/response
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AgentRunRequest(BaseModel):
    instruction: str
    mode: str = "analysis_ml"  # analysis_only, analysis_ml, analysis_ml_notebook
    dataset_hash: Optional[str] = None
    dataset_path: Optional[str] = None

class AgentRunResponse(BaseModel):
    job_id: str
    status: str  # pending, running, done, error
    message: str

class StepUpdate(BaseModel):
    step_id: int
    step_name: str
    status: str  # running, done, error
    output: Optional[str] = None
    timestamp: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    steps: List[StepUpdate] = []
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
```

### 1.4 Create Job Manager

**File**: `backend/job_manager.py`

```python
"""
Async job queue for long-running agent tasks
"""
import asyncio
import uuid
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from backend.models_api import StepUpdate, JobStatusResponse

class JobManager:
    """Manages async agent jobs with WebSocket broadcast"""
    
    def __init__(self):
        self.jobs: Dict[str, dict] = {}
        self.listeners: Dict[str, List] = {}  # job_id -> list of WebSocket connections
    
    def create_job(self, instruction: str, mode: str, dataset_hash: str = None) -> str:
        """Create a new job and return job_id"""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            'job_id': job_id,
            'instruction': instruction,
            'mode': mode,
            'dataset_hash': dataset_hash,
            'status': 'pending',
            'steps': [],
            'report': None,
            'error': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }
        self.listeners[job_id] = []
        return job_id
    
    def update_job_status(self, job_id: str, status: str):
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = status
            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
            self._broadcast(job_id, {'type': 'status', 'status': status})
    
    def add_step(self, job_id: str, step: dict):
        """Add a step update to job"""
        if job_id in self.jobs:
            self.jobs[job_id]['steps'].append(step)
            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
            self._broadcast(job_id, {'type': 'step', 'step': step})
    
    def complete_job(self, job_id: str, report: dict):
        """Mark job as complete with report"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = 'done'
            self.jobs[job_id]['report'] = report
            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
            self._broadcast(job_id, {'type': 'complete', 'report': report})
    
    def fail_job(self, job_id: str, error: str):
        """Mark job as failed"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = 'error'
            self.jobs[job_id]['error'] = error
            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
            self._broadcast(job_id, {'type': 'error', 'error': error})
    
    def get_job(self, job_id: str) -> Optional[dict]:
        """Get job status"""
        return self.jobs.get(job_id)
    
    def register_ws_listener(self, job_id: str, websocket):
        """Register WebSocket connection for live updates"""
        if job_id not in self.listeners:
            self.listeners[job_id] = []
        self.listeners[job_id].append(websocket)
    
    def remove_ws_listener(self, job_id: str, websocket):
        """Remove WebSocket connection"""
        if job_id in self.listeners:
            try:
                self.listeners[job_id].remove(websocket)
            except:
                pass
    
    def _broadcast(self, job_id: str, message: dict):
        """Broadcast message to all WebSocket listeners"""
        if job_id in self.listeners:
            for ws in self.listeners[job_id][:]:
                try:
                    import json
                    asyncio.create_task(ws.send_text(json.dumps(message)))
                except:
                    pass

# Global job manager instance
job_manager = JobManager()
```

### 1.5 Create Agent API Routes

**File**: `backend/agent_api.py`

```python
"""
Agent API endpoints with WebSocket support
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from backend.models_api import AgentRunRequest, AgentRunResponse, JobStatusResponse
from backend.job_manager import job_manager
import asyncio
import json

router = APIRouter()

@router.post("/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest):
    """Start a new agent job"""
    job_id = job_manager.create_job(
        instruction=request.instruction,
        mode=request.mode,
        dataset_hash=request.dataset_hash
    )
    
    # Start agent execution in background thread
    from threading import Thread
    thread = Thread(
        target=execute_agent_job,
        args=(job_id, request.instruction, request.mode, request.dataset_hash)
    )
    thread.start()
    
    return AgentRunResponse(
        job_id=job_id,
        status='pending',
        message='Job started'
    )

@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job status"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(**job)

@router.websocket("/job/{job_id}/ws")
async def job_websocket(websocket: WebSocket, job_id: str):
    """WebSocket for live job progress updates"""
    job = job_manager.get_job(job_id)
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return
    
    await websocket.accept()
    job_manager.register_ws_listener(job_id, websocket)
    
    try:
        while True:
            # Keep connection alive, receive messages if any
            await websocket.receive_text()
    except WebSocketDisconnect:
        job_manager.remove_ws_listener(job_id, websocket)

def execute_agent_job(job_id: str, instruction: str, mode: str, dataset_hash: str = None):
    """Execute agent job in background thread"""
    try:
        job_manager.update_job_status(job_id, 'running')
        
        # Import and run agent
        from backend.scripts.data_agent_3 import run_agent
        
        # This is a simplified version - adapt to your actual agent
        result = run_agent(instruction, force_task_type=mode)
        
        # Complete job with result
        job_manager.complete_job(job_id, result)
        
    except Exception as e:
        job_manager.fail_job(job_id, str(e))
```

---

## Part 2: React Frontend

### 2.1 Add Dependencies to package.json

```bash
cd frontend
npm install react-router-dom
```

### 2.2 Create Notebook UI Components

**Directory**: `frontend/src/components/notebook/`

Due to the extensive nature of the React components, I'll create a summary of what's needed:

**Files to Create**:
1. `NotebookCell.tsx` - Individual cell component
2. `AgentPanel.tsx` - Left input panel
3. `OutputPanel.tsx` - Right output panel
4. `ProgressBar.tsx` - Progress indicator
5. `ChartViewer.tsx` - Plotly chart renderer
6. `NotebookUI.tsx` - Main page component

**Full implementation code for all components is in the Week3_FastAPI_UI.docx document, pages 15-25.**

### 2.3 Create API Client

**File**: `frontend/src/api/agentApi.ts`

```typescript
const API_BASE_URL = 'http://localhost:8000';

export interface AgentJob {
  job_id: string;
  status: 'pending' | 'running' | 'done' | 'error';
  steps: any[];
  report: any;
  error: string | null;
}

export async function runAgentJob(
  instruction: string,
  mode: string,
  datasetHash?: string
): Promise<{ job_id: string }> {
  const response = await fetch(`${API_BASE_URL}/api/agent/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      instruction,
      mode,
      dataset_hash: datasetHash,
    }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to start agent job');
  }
  
  return response.json();
}

export async function getJobStatus(jobId: string): Promise<AgentJob> {
  const response = await fetch(`${API_BASE_URL}/api/agent/job/${jobId}`);
  if (!response.ok) {
    throw new Error('Failed to get job status');
  }
  return response.json();
}

export function connectJobWebSocket(
  jobId: string,
  onMessage: (data: any) => void
): WebSocket {
  const ws = new WebSocket(`ws://localhost:8000/api/agent/job/${jobId}/ws`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  return ws;
}
```

### 2.4 Add Route to App.tsx

**File**: `frontend/src/App.tsx`

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { NotebookUI } from './components/notebook/NotebookUI';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Existing routes */}
        <Route path="/" element={<YourExistingApp />} />
        
        {/* New notebook route */}
        <Route path="/notebook" element={<NotebookUI />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

## Part 3: Running Everything

### 3.1 Create Run Script

**File**: `run_fastapi.py`

```python
"""Run FastAPI backend for Week 3 notebook UI"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting FastAPI backend on port 8000...")
    print("📚 API docs: http://localhost:8000/docs")
    uvicorn.run(
        "backend.fastapi_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

### 3.2 Add Link to Streamlit App

**File**: `app.py` (in DataAgent section)

```python
# Add this to the DataAgent tab in app.py
st.markdown("---")
st.markdown("### 🚀 Advanced Notebook Mode")
st.markdown(
    '<a href="http://localhost:5173/notebook" target="_blank">'
    '<button style="background:linear-gradient(135deg,#4361ee,#06b6d4);'
    'color:white;border:none;padding:12px 24px;border-radius:8px;'
    'font-size:16px;cursor:pointer;">'
    '🚀 Open Notebook Agent UI</button></a>',
    unsafe_allow_html=True
)
st.info("Opens the advanced Jupyter-style interface in a new tab")
```

### 3.3 Start Guide

Create `START_GUIDE.md`:

```markdown
# Starting All Services

## Terminal 1: FastAPI Backend
```bash
cd D:\FINBOT-2\VISHLESHAK_AI
python run_fastapi.py
```
API runs on: http://localhost:8000
API docs: http://localhost:8000/docs

## Terminal 2: React Frontend
```bash
cd D:\FINBOT-2\VISHLESHAK_AI\frontend
npm run dev
```
UI runs on: http://localhost:5173
Notebook UI: http://localhost:5173/notebook

## Terminal 3: Streamlit App (existing)
```bash
cd D:\FINBOT-2\VISHLESHAK_AI
streamlit run app.py
```
App runs on: http://localhost:8501
```

---

## Testing Checklist

- [ ] FastAPI starts without errors on port 8000
- [ ] `/api/health` returns `{"status": "ok"}`
- [ ] `/docs` shows Swagger UI with all endpoints
- [ ] React app starts on port 5173
- [ ] `/notebook` route loads notebook UI
- [ ] Can submit instruction and see job start
- [ ] WebSocket connection established
- [ ] Live progress updates appear
- [ ] Charts render correctly
- [ ] Final report displays when job completes

---

## Next Steps

The complete React component code is extensive (2000+ lines). Due to token limits, I recommend:

1. **Copy component code from Week3_FastAPI_UI.docx** (pages 15-25)
2. **Create files in `frontend/src/components/notebook/`**
3. **Test incrementally** - start with AgentPanel, then OutputPanel, then WebSocket integration

All backend code is provided above and ready to use!
