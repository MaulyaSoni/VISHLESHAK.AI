"""Python sandbox tool - executes snippet safely with timeout in subprocess"""
import tempfile
import subprocess
import sys
import json
import os
from typing import Dict

class PythonSandboxTool:
    name = "python_sandbox"
    description = "Execute a short python snippet in a subprocess with timeout (restricted)."

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def run(self, code: str) -> Dict:
        # write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            fname = f.name
        try:
            proc = subprocess.run([sys.executable, fname], capture_output=True, text=True, timeout=self.timeout)
            return {"stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
        except subprocess.TimeoutExpired as e:
            return {"error": "timeout", "detail": str(e)}
        except Exception as e:
            return {"error": str(e)}
        finally:
            try:
                os.remove(fname)
            except Exception:
                pass
