"""
Tests for Tool System
"""
import unittest
import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.tool_registry import ToolRegistry, BaseTool, get_tool_registry
from tools.langchain_tools.calculator import CalculatorTool
from tools.langchain_tools.python_repl import PythonREPLTool
from tools.custom_tools.data_transformer import DataTransformerTool


class TestToolSystem(unittest.TestCase):
    
    def setUp(self):
        self.registry = get_tool_registry()
    
    def test_registry_singleton(self):
        """Test that registry is a singleton"""
        reg2 = get_tool_registry()
        self.assertIs(self.registry, reg2)
    
    def test_calculator(self):
        """Test Calculator Tool"""
        calc = CalculatorTool()
        result = calc.run("2+2")
        self.assertEqual(result, 4.0)
    
    def test_python_repl_safe(self):
        """Test Python REPL Tool with safe code"""
        repl = PythonREPLTool()
        result = repl.run("result = 2 + 3\nprint(result)")
        self.assertTrue(result['success'])
    
    def test_python_repl_unsafe(self):
        """Test Python REPL blocks unsafe code"""
        repl = PythonREPLTool()
        result_unsafe = repl.run("import os; os.system('ls')")
        self.assertFalse(result_unsafe['success'])
        # Should contain some indication of blocked operation
        error_msg = result_unsafe.get('error', '') or result_unsafe.get('output', '')
        self.assertTrue(
            "Restricted" in error_msg or "Dangerous" in error_msg or "blocked" in error_msg.lower(),
            f"Error message '{error_msg}' doesn't indicate blocked operation"
        )
    
    def test_data_transformer_filter(self):
        """Test Data Transformer filter operation"""
        transformer = DataTransformerTool()
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "score": [85, 92, 78]
        })
        result = transformer.run(df, operation="filter", condition="score > 80")
        self.assertEqual(len(result), 2)
    
    def test_data_transformer_sort(self):
        """Test Data Transformer sort operation"""
        transformer = DataTransformerTool()
        df = pd.DataFrame({
            "name": ["Charlie", "Alice", "Bob"],
            "score": [78, 85, 92]
        })
        result = transformer.run(df, operation="sort", by="score", ascending=True)
        self.assertEqual(result.iloc[0]["name"], "Charlie")
        self.assertEqual(result.iloc[-1]["name"], "Bob")
    
    def test_tool_registration(self):
        """Test tool listing"""
        tools = self.registry.list_tools()
        self.assertTrue(len(tools) > 0)
        tool_names = [t["name"] for t in tools]
        self.assertIn("calculator", tool_names)
        self.assertIn("python_repl", tool_names)
    
    def test_base_tool_enable_disable(self):
        """Test enable/disable"""
        tool = BaseTool(name="test_tool", description="test", category="test")
        self.assertTrue(tool.enabled)
        tool.disable()
        self.assertFalse(tool.enabled)
        tool.enable()
        self.assertTrue(tool.enabled)


class TestMemorySystem(unittest.TestCase):
    """Test the enhanced memory system"""
    
    def test_memory_manager_init(self):
        """Test ChatMemoryManager initializes"""
        from core.memory import ChatMemoryManager
        
        # Use temp db path for testing
        import tempfile
        db_path = os.path.join(tempfile.gettempdir(), "test_finbot_memory.db")
        
        mem = ChatMemoryManager(session_id="test_session", db_path=db_path)
        self.assertIsNotNone(mem)
        
        # Test add/get messages
        mem.add_message("test_session", "human", "Hello")
        mem.add_message("test_session", "ai", "Hi there!")
        
        messages = mem.get_messages("test_session")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['type'], 'human')
        self.assertEqual(messages[1]['type'], 'ai')
        
        # Test data context
        mem.save_data_context("Test summary", ["col1", "col2"])
        ctx = mem.get_data_context()
        self.assertEqual(ctx["summary"], "Test summary")
        self.assertEqual(ctx["columns"], ["col1", "col2"])
        
        # Cleanup
        mem.clear_session("test_session")
        try:
            os.unlink(db_path)
        except PermissionError:
            pass  # Windows file lock
    
    def test_memory_variables(self):
        """Test get_memory_variables returns LangChain format"""
        from core.memory import ChatMemoryManager
        
        import tempfile
        db_path = os.path.join(tempfile.gettempdir(), "test_finbot_memory2.db")
        
        mem = ChatMemoryManager(session_id="test2", db_path=db_path)
        mem.add_message("test2", "human", "Test question")
        mem.add_message("test2", "ai", "Test answer")
        
        variables = mem.get_memory_variables()
        self.assertIn("chat_history", variables)
        self.assertEqual(len(variables["chat_history"]), 2)
        
        # Cleanup
        mem.clear_session("test2")
        try:
            os.unlink(db_path)
        except PermissionError:
            pass  # Windows file lock


if __name__ == '__main__':
    unittest.main()
