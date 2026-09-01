"""
Run FastAPI server
===================
Starts the Week 3 FastAPI backend on port 8000

Usage:
  python run_fastapi.py
  
Then visit:
  - API Docs: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health
"""

import sys
import os

# Ensure we're using the right Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("=" * 60)
    print("  Vishleshak AI - FastAPI Backend (Week 3)")
    print("=" * 60)
    print()
    print("Starting server on http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print()
    
    # Import here to ensure path is set
    import uvicorn
    from backend.fastapi_main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, log_level="info")
