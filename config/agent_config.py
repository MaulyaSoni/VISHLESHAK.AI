"""
Agent Configuration for Vishleshak AI
Complete agentic system settings
"""

# Agent behavior
AGENT_TYPE = "react"
MAX_ITERATIONS = 15
MAX_EXECUTION_TIME = 120
AGENT_TEMPERATURE = 0.3
VERBOSE = True

# Tool selection
SMART_TOOL_SELECTION = True
MAX_TOOLS_PER_QUERY = 5
TOOL_SELECTION_STRATEGY = "hybrid"
TRACK_TOOL_PERFORMANCE = True

# Reflection & self-correction
ENABLE_REFLECTION = True
MIN_CONFIDENCE_THRESHOLD = 0.7
MAX_REFLECTION_RETRIES = 2

# Memory
STORE_TOOL_HISTORY = True
MAX_TOOL_HISTORY = 100
ENABLE_TOOL_LEARNING = True

# Planning
ENABLE_PLANNING = True
SHOW_PLAN = True
MAX_PLAN_STEPS = 8

# Fallback
ENABLE_FALLBACK = True
FALLBACK_AFTER_ITERATIONS = 10

# Tool settings
TOOL_SETTINGS = {
    "statistical_analyzer": {"max_columns": 50, "confidence_level": 0.95},
    "correlation_finder": {"min_correlation": 0.3, "method": "pearson"},
    "anomaly_detector": {"contamination": 0.1, "method": "isolation_forest"},
    "chart_generator": {"max_charts": 10, "interactive": True},
    "trend_analyzer": {"min_data_points": 10, "detect_seasonality": True},
    "forecaster": {"default_horizon": 12, "method": "auto"},
    "python_sandbox": {"timeout": 30, "max_memory_mb": 512},
    "report_generator": {"format": "pdf", "include_charts": True},
}

# Advanced RAG
ADVANCED_RAG = {
    "multi_query": {"enabled": True, "num_queries": 3},
    "compression": {"enabled": True, "compression_ratio": 0.5},
    "ensemble": {"enabled": True, "weights": [0.5, 0.3, 0.2]},
    "self_query": {"enabled": True},
}

# UI
UI_SETTINGS = {
    "show_thinking": "toggle",
    "show_tool_calls": True,
    "show_confidence": True,
    "animate_thinking": True,
}
