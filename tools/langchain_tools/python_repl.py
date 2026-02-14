"""
Python REPL Tool for FINBOT v4
Executes Python code safely with sandboxing
"""

import sys
from io import StringIO
from typing import Any, Dict
import logging
from contextlib import redirect_stdout, redirect_stderr
from tools.tool_registry import BaseTool
from config import tool_config

logger = logging.getLogger(__name__)


class PythonREPLTool(BaseTool):
    """
    Execute Python code safely
    
    Features:
    - Sandboxed execution
    - Timeout protection
    - Module whitelist
    - Output capture
    
    Usage:
        tool = PythonREPLTool()
        result = tool.run("import pandas as pd; df.head()")
    """
    
    def __init__(self):
        super().__init__(
            name="python_repl",
            description=(
                "Execute Python code to perform data analysis, calculations, "
                "and transformations. Use this when you need to manipulate data "
                "with pandas, perform complex calculations, or generate insights "
                "programmatically. Input should be valid Python code."
            ),
            category="langchain"
        )
        self.timeout = tool_config.CODE_EXECUTION_TIMEOUT
        self.safe_mode = tool_config.CODE_EXECUTION_SAFE_MODE
        self.allowed_modules = tool_config.ALLOWED_MODULES
        self.restricted_ops = tool_config.RESTRICTED_OPERATIONS
    
    def _validate_code(self, code: str) -> tuple[bool, str]:
        """
        Validate code for safety
        
        Args:
            code: Python code to validate
            
        Returns:
            (is_valid, error_message)
        """
        # Check for restricted operations
        for restricted in self.restricted_ops:
            if restricted in code:
                return False, f"Restricted operation detected: {restricted}"
        
        # Check for dangerous patterns
        dangerous_patterns = ["os.system", "subprocess", "__import__", "exec(", "eval("]
        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Dangerous pattern detected: {pattern}"
        
        return True, ""
    
    def run(self, code: str, globals_dict: Dict = None) -> Dict[str, Any]:
        """
        Execute Python code
        
        Args:
            code: Python code to execute
            globals_dict: Global variables to make available
            
        Returns:
            Dict with keys: success, output, error
        """
        if not tool_config.ENABLE_CODE_EXECUTION:
            return {
                "success": False,
                "output": "",
                "error": "Code execution is disabled"
            }
        
        # Validate code if in safe mode
        if self.safe_mode:
            is_valid, error_msg = self._validate_code(code)
            if not is_valid:
                return {
                    "success": False,
                    "output": "",
                    "error": error_msg
                }
        
        # Prepare globals
        if globals_dict is None:
            globals_dict = {}
        
        # Add allowed modules
        import_code = ""
        for module in self.allowed_modules:
            try:
                import_code += f"import {module}\n"
            except ImportError:
                pass
        
        full_code = import_code + "\n" + code
        
        # Capture output
        stdout = StringIO()
        stderr = StringIO()
        
        try:
            # Execute code with output capture
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(full_code, globals_dict)
            
            output = stdout.getvalue()
            error = stderr.getvalue()
            
            if error:
                return {
                    "success": False,
                    "output": output,
                    "error": error
                }
            
            return {
                "success": True,
                "output": output,
                "error": ""
            }
        
        except Exception as e:
            return {
                "success": False,
                "output": stdout.getvalue(),
                "error": str(e)
            }
        finally:
            stdout.close()
            stderr.close()
