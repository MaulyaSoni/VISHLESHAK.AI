"""
Data Agent Modal Integration
Wraps the Modal sandbox for use by data_agent_3.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modal_sandbox import run_code_remote


class ModalCodeExecutor:
    """
    Execute agent-generated code in Modal sandbox.
    Drop-in replacement for direct exec() calls.
    """
    
    def __init__(self, fallback_local: bool = None):
        """
        Initialize executor.
        
        Args:
            fallback_local: If None, reads from MODAL_FALLBACK_LOCAL env var
        """
        if fallback_local is None:
            fallback_local = os.environ.get('MODAL_FALLBACK_LOCAL', 'true').lower() == 'true'
        self.fallback_local = fallback_local
    
    def execute(self, code: str, dataset_path: str = None) -> dict:
        """
        Execute code in sandbox.
        
        Args:
            code: Python code to execute
            dataset_path: Optional path to dataset file
        
        Returns:
            dict with:
                - success: bool
                - outputs: dict (values from _outputs)
                - charts: list of chart paths
                - stdout: captured output
                - error: error message (if failed)
        """
        print(f"🔒 Executing code in {'LOCAL' if self.fallback_local else 'MODAL'} sandbox...")
        
        try:
            result = run_code_remote(
                code,
                dataset_path=dataset_path,
                fallback_local=self.fallback_local
            )
            
            if result['success']:
                print(f"✅ Code executed successfully")
                if result.get('outputs'):
                    print(f"   Outputs: {list(result['outputs'].keys())}")
                if result.get('charts'):
                    print(f"   Charts generated: {len(result['charts'])}")
            else:
                print(f"❌ Code execution failed: {result.get('error', 'Unknown error')[:100]}")
            
            return result
            
        except Exception as e:
            print(f"❌ Sandbox execution error: {e}")
            return {
                'success': False,
                'outputs': {},
                'charts': [],
                'stdout': '',
                'error': str(e),
            }
    
    def execute_and_extract(self, code: str, key: str, default=None):
        """
        Execute code and extract a specific output key.
        
        Args:
            code: Python code
            key: Key to extract from _outputs
            default: Default value if key not found
        
        Returns:
            Value of outputs[key] or default
        """
        result = self.execute(code)
        if result['success']:
            return result['outputs'].get(key, default)
        return default


# Global executor instance
_executor = None

def get_executor() -> ModalCodeExecutor:
    """Get or create the global executor instance."""
    global _executor
    if _executor is None:
        _executor = ModalCodeExecutor()
    return _executor


def execute_in_sandbox(code: str, dataset_path: str = None) -> dict:
    """
    Convenience function: Execute code in sandbox.
    
    This is the main function that data_agent_3.py should call
    instead of using exec() directly.
    
    Args:
        code: Python code to execute
        dataset_path: Optional dataset path
    
    Returns:
        Execution result dict
    """
    return get_executor().execute(code, dataset_path)
