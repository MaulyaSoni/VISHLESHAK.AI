"""
Entry point proxy for backend.fastapi_main
"""
import sys
from pathlib import Path

# Add directories to system path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from fastapi_main import app
