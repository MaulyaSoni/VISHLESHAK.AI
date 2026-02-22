"""
Tool Registry for Vishleshak AI v1
Central registry for all tools (LangChain and custom)
"""

from typing import Dict, List, Any, Optional, Callable
import logging
from config import tool_config

logger = logging.getLogger(__name__)


class BaseTool:
    """
    Base class for all tools
    
    All tools must inherit from this and implement the run() method
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        func: Optional[Callable] = None
    ):
        """
        Initialize base tool
        
        Args:
            name: Tool name (unique identifier)
            description: Tool description (for LLM to understand)
            category: Tool category (langchain, visualization, data, analysis)
            func: Optional function to execute
        """
        self.name = name
        self.description = description
        self.category = category
        self.func = func
        self.enabled = True
    
    def run(self, *args, **kwargs) -> Any:
        """
        Execute the tool
        
        Must be implemented by subclasses or provided as func
        """
        if self.func:
            return self.func(*args, **kwargs)
        raise NotImplementedError("Tool must implement run() method or provide func")
    
    def __call__(self, *args, **kwargs) -> Any:
        """Make tool callable"""
        return self.run(*args, **kwargs)
    
    def enable(self):
        """Enable the tool"""
        self.enabled = True
    
    def disable(self):
        """Disable the tool"""
        self.enabled = False


class ToolRegistry:
    """
    Central registry for all tools
    
    Features:
    - Register tools
    - Get tools by name or category
    - Enable/disable tools
    - List available tools
    
    Usage:
        registry = ToolRegistry()
        registry.register_tool(my_tool)
        tool = registry.get_tool("python_repl")
    """
    
    _instance = None  # Singleton
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize tool registry"""
        if not hasattr(self, 'initialized'):
            self.tools: Dict[str, BaseTool] = {}
            self.initialized = True
            logger.info("✅ Tool registry initialized")
    
    def register_tool(self, tool: BaseTool) -> bool:
        """
        Register a tool
        
        Args:
            tool: Tool instance to register
            
        Returns:
            True if successful, False if tool already exists
        """
        if tool.name in self.tools:
            logger.warning(f"Tool already registered: {tool.name}")
            return False
        
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
        return True
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        tool = self.tools.get(name)
        if not tool:
            logger.warning(f"Tool not found: {name}")
        return tool
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """
        Get all tools in a category
        
        Args:
            category: Category name
            
        Returns:
            List of tools in category
        """
        return [
            tool for tool in self.tools.values()
            if tool.category == category and tool.enabled
        ]
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get all enabled tools"""
        return [tool for tool in self.tools.values() if tool.enabled]
    
    def list_tools(self) -> List[Dict[str, str]]:
        """
        List all tools with their info
        
        Returns:
            List of dicts with tool info
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "enabled": tool.enabled
            }
            for tool in self.tools.values()
        ]
    
    def enable_tool(self, name: str) -> bool:
        """Enable a tool"""
        tool = self.get_tool(name)
        if tool:
            tool.enable()
            return True
        return False
    
    def disable_tool(self, name: str) -> bool:
        """Disable a tool"""
        tool = self.get_tool(name)
        if tool:
            tool.disable()
            return True
        return False


# Global instance
def get_tool_registry() -> ToolRegistry:
    """Get global tool registry instance"""
    return ToolRegistry()
