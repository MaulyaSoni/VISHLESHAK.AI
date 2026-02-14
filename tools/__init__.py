"""
Tools Module for FINBOT v4
Initializes and registers all tools
"""

from tools.tool_registry import ToolRegistry, BaseTool, get_tool_registry
from tools.langchain_tools.python_repl import PythonREPLTool
from tools.langchain_tools.calculator import CalculatorTool
from tools.custom_tools.chart_generator import ChartGeneratorTool
from tools.custom_tools.data_transformer import DataTransformerTool
from tools.custom_tools.export_tool import ExportTool
import logging

logger = logging.getLogger(__name__)


def initialize_all_tools():
    """
    Initialize and register all tools
    
    This should be called on application startup
    """
    logger.info("Initializing all tools...")
    
    registry = get_tool_registry()
    
    # Tier 1: Essential Tools
    tools_to_register = [
        PythonREPLTool(),
        CalculatorTool(),
        ChartGeneratorTool(),
        DataTransformerTool(),
        ExportTool()
    ]
    
    for tool in tools_to_register:
        registry.register_tool(tool)
    
    logger.info(f"✅ Registered {len(tools_to_register)} tools")
    
    return registry


# Auto-initialize on import
_registry = initialize_all_tools()
