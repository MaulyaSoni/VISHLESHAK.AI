"""
Vishleshak AI — Modal Execution Sandbox
All agent-generated Python code runs here, NOT on the host machine.
Modal spins up an isolated container, runs the code, returns results.
"""
# Load environment variables FIRST (before modal import)
from dotenv import load_dotenv
load_dotenv()

import modal
import os
import json
import traceback
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# MODAL APP & IMAGE DEFINITION
# ─────────────────────────────────────────────────────────────────────────────

app = modal.App("vishleshak-sandbox")

# Define the sandbox image with all required packages
sandbox_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install([
        # Data science stack
        "pandas==2.2.2",
        "numpy==1.26.4",
        "scikit-learn==1.4.0",
        "xgboost==2.0.3",
        "shap==0.45.0",
        "plotly==5.20.0",
        "kaleido==0.2.1",
        # Notebook
        "nbformat==5.10.4",
        "nbconvert==7.16.3",
        "jupyter==1.1.1",
        # Utilities
        "requests==2.31.0",
        "python-dotenv==1.0.1",
    ])
)

# Persistent volume for outputs (charts, notebooks, etc.)
VOLUME_PATH = "/outputs"
output_volume = modal.Volume.from_name("vishleshak-outputs", create_if_missing=True)


# ─────────────────────────────────────────────────────────────────────────────
# SANDBOX EXECUTION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

@app.function(
    image=sandbox_image,
    volumes={VOLUME_PATH: output_volume},
    timeout=600,  # 10 minutes default (configurable via .env)
    cpu=2.0,
    memory=2048,  # 2GB RAM
)
def execute_code_in_sandbox(code: str, dataset_path: str = None) -> dict:
    """
    Execute Python code in an isolated Modal container.
    
    Args:
        code: Python code to execute (agent-generated)
        dataset_path: Optional path to dataset file in /outputs
    
    Returns:
        dict with keys:
            - success: bool
            - outputs: dict (values set via _outputs in code)
            - charts: list of chart file paths
            - notebook_path: path to generated notebook (if any)
            - error: error message (if success=False)
            - stdout: captured stdout
    """
    import sys
    from io import StringIO
    import subprocess
    
    # Setup execution environment
    _outputs = {}
    stdout_capture = StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture
    
    try:
        # If dataset_path provided, load it into the namespace
        exec_globals = {
            '_outputs': _outputs,
            '__builtins__': __builtins__,
        }
        
        if dataset_path:
            import pandas as pd
            exec_globals['pd'] = pd
            exec_globals['dataset_path'] = dataset_path
        
        # Execute the agent-generated code
        exec(code, exec_globals)
        
        # Capture outputs
        sys.stdout = old_stdout
        stdout_text = stdout_capture.getvalue()
        
        # Collect chart files
        charts = []
        if os.path.exists(VOLUME_PATH):
            for f in os.listdir(VOLUME_PATH):
                if f.endswith(('.png', '.jpg', '.jpeg', '.html')):
                    charts.append(os.path.join(VOLUME_PATH, f))
        
        # Persist volume changes
        output_volume.commit()
        
        return {
            'success': True,
            'outputs': _outputs,
            'charts': charts,
            'notebook_path': _outputs.get('notebook_path'),
            'stdout': stdout_text,
            'error': None,
        }
        
    except Exception as e:
        sys.stdout = old_stdout
        error_traceback = traceback.format_exc()
        
        return {
            'success': False,
            'outputs': _outputs,
            'charts': [],
            'notebook_path': None,
            'stdout': stdout_capture.getvalue(),
            'error': str(e),
            'traceback': error_traceback,
        }


# ─────────────────────────────────────────────────────────────────────────────
# LOCAL FALLBACK (for development when Modal is unavailable)
# ─────────────────────────────────────────────────────────────────────────────

def run_code_local(code: str, dataset_path: str = None, timeout: int = 300) -> dict:
    """
    Run code locally as fallback (development mode only).
    WARNING: This executes code on the host machine - only use for testing!
    """
    import sys
    from io import StringIO
    import traceback
    
    _outputs = {}
    stdout_capture = StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture
    
    try:
        exec_globals = {
            '_outputs': _outputs,
            '__builtins__': __builtins__,
        }
        
        if dataset_path:
            import pandas as pd
            exec_globals['pd'] = pd
            exec_globals['dataset_path'] = dataset_path
        
        # Execute code (note: timeout not enforced on Windows in local mode)
        # For production, use Modal which enforces timeouts
        exec(code, exec_globals)
        
        sys.stdout = old_stdout
        
        return {
            'success': True,
            'outputs': _outputs,
            'charts': [],
            'notebook_path': _outputs.get('notebook_path'),
            'stdout': stdout_capture.getvalue(),
            'error': None,
        }
        
    except TimeoutError as e:
        sys.stdout = old_stdout
        return {
            'success': False,
            'outputs': _outputs,
            'charts': [],
            'notebook_path': None,
            'stdout': stdout_capture.getvalue(),
            'error': str(e),
            'traceback': traceback.format_exc(),
        }
        
    except Exception as e:
        sys.stdout = old_stdout
        return {
            'success': False,
            'outputs': _outputs,
            'charts': [],
            'notebook_path': None,
            'stdout': stdout_capture.getvalue(),
            'error': str(e),
            'traceback': traceback.format_exc(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def run_code_remote(code: str, dataset_path: str = None, fallback_local: bool = True) -> dict:
    """
    Main entry point: Run code in Modal sandbox with local fallback.
    
    This function is called by data_agent_3.py instead of exec().
    
    Args:
        code: Python code to execute
        dataset_path: Optional path to dataset
        fallback_local: If True, fall back to local execution if Modal unavailable
    
    Returns:
        dict with execution results
    """
    # Check if Modal is available
    modal_available = os.environ.get('MODAL_TOKEN_ID') or os.environ.get('MODAL_TOKEN_SECRET')
    
    if not modal_available and fallback_local:
        # Fallback to local execution
        print("⚠️  Modal not configured — using LOCAL execution (development mode)")
        print("   Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in .env for sandbox mode")
        timeout = int(os.environ.get('MODAL_TIMEOUT', 300))
        return run_code_local(code, dataset_path, timeout=timeout)
    
    if not modal_available:
        raise RuntimeError(
            "Modal not configured. Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in .env\n"
            "Run: modal token new"
        )
    
    # Run on Modal
    try:
        timeout = int(os.environ.get('MODAL_TIMEOUT', 600))
        
        # Deploy the function if not already deployed
        result = execute_code_in_sandbox.remote(code, dataset_path)
        return result
        
    except Exception as e:
        if fallback_local:
            print(f"⚠️  Modal execution failed: {e}")
            print("   Falling back to local execution")
            return run_code_local(code, dataset_path)
        else:
            raise


def upload_file_to_volume(local_path: str, volume_path: str) -> str:
    """
    Upload a file to the Modal volume.
    
    Args:
        local_path: Path to file on host machine
        volume_path: Destination path in volume (e.g., '/outputs/dataset.csv')
    
    Returns:
        Path in volume
    """
    import shutil
    
    # Copy file to volume mount point
    dest_path = os.path.join(os.getcwd(), volume_path.lstrip('/'))
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy2(local_path, dest_path)
    
    # Commit volume
    output_volume.commit()
    
    return volume_path


def download_file_from_volume(volume_path: str, local_path: str) -> str:
    """
    Download a file from the Modal volume.
    
    Args:
        volume_path: Path in volume (e.g., '/outputs/chart.png')
        local_path: Destination path on host machine
    
    Returns:
        Local file path
    """
    import shutil
    
    # Reload volume
    output_volume.reload()
    
    # Copy file from volume
    src_path = os.path.join(os.getcwd(), volume_path.lstrip('/'))
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    shutil.copy2(src_path, local_path)
    
    return local_path
