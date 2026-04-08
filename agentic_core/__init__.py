"""
Vishleshak AI Agentic Core
"""

__all__ = [
    "VishleshakReActAgent",
    "create_vishleshak_agent",
    "AgentMemory",
    "get_agent_memory",
    "ToolSelector",
    "ReflectionLayer",
    "invoke_supervisor",
    "get_supervisor_graph",
    "VishleshakState",
    "run_proactive_scan",
    "get_scheduler_manager",
    "parse_nl_schedule",
]

def __getattr__(name):
    """Lazy imports to avoid circular dependencies"""
    if name == "create_vishleshak_agent" or name == "VishleshakReActAgent":
        from .react_agent import VishleshakReActAgent, create_vishleshak_agent
        return create_vishleshak_agent if name == "create_vishleshak_agent" else VishleshakReActAgent
    
    if name == "get_agent_memory" or name == "AgentMemory":
        try:
            from .agent_memory import AgentMemory, get_agent_memory
            return get_agent_memory if name == "get_agent_memory" else AgentMemory
        except:
            return None
    
    if name == "ToolSelector":
        try:
            from .tool_selector import ToolSelector
            return ToolSelector
        except:
            return None
    
    if name == "ReflectionLayer":
        try:
            from .reflection_layer import ReflectionLayer
            return ReflectionLayer
        except:
            return None
    
    if name == "invoke_supervisor" or name == "get_supervisor_graph" or name == "VishleshakState":
        from .supervisor_graph import invoke_supervisor, get_supervisor_graph, VishleshakState
        if name == "invoke_supervisor":
            return invoke_supervisor
        elif name == "get_supervisor_graph":
            return get_supervisor_graph
        else:
            return VishleshakState
    
    if name == "run_proactive_scan":
        try:
            from .proactive_engine import run_proactive_scan
            return run_proactive_scan
        except:
            return None
    
    if name == "get_scheduler_manager" or name == "parse_nl_schedule":
        try:
            from .scheduler import get_scheduler_manager, parse_nl_schedule
            return get_scheduler_manager if name == "get_scheduler_manager" else parse_nl_schedule
        except:
            return None
    
    raise AttributeError(f"module has no attribute '{name}'")