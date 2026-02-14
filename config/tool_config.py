"""
Tool System Configuration for FINBOT v4
Handles all tool-related settings and configurations
"""
import os
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
EXPORT_DIR = STORAGE_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# TOOL CATEGORIES
# ============================================================================

# Available tool categories
TOOL_CATEGORIES = {
    "langchain": ["python_repl", "calculator", "search", "wikipedia"],
    "visualization": ["chart_generator"],
    "data": ["data_transformer", "export"],
    "analysis": ["forecaster", "what_if", "root_cause", "anomaly_detector"],
    "rag": ["rag_retrieval"]
}

# Tool tier classification
TOOL_TIERS = {
    "tier1_essential": ["python_repl", "calculator", "rag_retrieval",
                        "chart_generator", "data_transformer", "export"],
    "tier2_useful": ["search", "wikipedia", "forecaster", "what_if"],
    "tier3_advanced": ["root_cause", "anomaly_detector", "csv_agent"]
}

# ============================================================================
# CODE EXECUTION SETTINGS
# ============================================================================

# Python REPL Tool
ENABLE_CODE_EXECUTION = True
CODE_EXECUTION_TIMEOUT = 30  # seconds
CODE_EXECUTION_SAFE_MODE = True  # Use sandboxing

# Allowed Python modules for code execution
ALLOWED_MODULES = [
    "pandas", "numpy", "math", "statistics", "datetime",
    "collections", "itertools", "functools"
]

# Restricted operations
RESTRICTED_OPERATIONS = [
    "eval", "exec", "compile", "__import__", "open", "file",
    "input", "raw_input", "execfile"
]

# ============================================================================
# CALCULATOR SETTINGS
# ============================================================================

ENABLE_CALCULATOR = True
CALCULATOR_PRECISION = 10  # Decimal places
CALCULATOR_TIMEOUT = 5  # seconds

# ============================================================================
# SEARCH SETTINGS
# ============================================================================

ENABLE_WEB_SEARCH = True
SEARCH_ENGINE = "duckduckgo"  # or "google" (requires API key)
SEARCH_MAX_RESULTS = 5
SEARCH_TIMEOUT = 10  # seconds

# Search safety
SEARCH_SAFE_MODE = True  # Filter adult content

# ============================================================================
# WIKIPEDIA SETTINGS
# ============================================================================

ENABLE_WIKIPEDIA = True
WIKIPEDIA_MAX_RESULTS = 3
WIKIPEDIA_TIMEOUT = 10  # seconds
WIKIPEDIA_LANGUAGE = "en"

# ============================================================================
# VISUALIZATION SETTINGS
# ============================================================================

ENABLE_VISUALIZATION = True
DEFAULT_CHART_ENGINE = "plotly"  # or "matplotlib", "seaborn"

# Chart types supported
SUPPORTED_CHART_TYPES = [
    "scatter", "line", "bar", "histogram", "box", "violin",
    "heatmap", "pie", "area", "scatter_3d", "surface"
]

# Chart defaults
DEFAULT_CHART_WIDTH = 800
DEFAULT_CHART_HEIGHT = 600
DEFAULT_CHART_THEME = "plotly"  # or "plotly_white", "plotly_dark"

# Export formats for charts
CHART_EXPORT_FORMATS = ["png", "jpg", "svg", "html", "pdf"]

# ============================================================================
# DATA TRANSFORMATION SETTINGS
# ============================================================================

ENABLE_DATA_TRANSFORMATION = True

# Supported transformations
SUPPORTED_TRANSFORMATIONS = [
    "filter", "sort", "group_by", "aggregate", "pivot",
    "melt", "merge", "join", "fillna", "dropna",
    "normalize", "standardize", "one_hot_encode"
]

# Safety limits
MAX_ROWS_TRANSFORM = 100000  # Max rows for transformation
TRANSFORM_TIMEOUT = 30  # seconds

# ============================================================================
# EXPORT SETTINGS
# ============================================================================

ENABLE_EXPORT = True

# Export formats
EXPORT_FORMATS = ["xlsx", "csv", "json", "pdf", "html"]
DEFAULT_EXPORT_FORMAT = "xlsx"

# Export limits
MAX_EXPORT_ROWS = 100000
MAX_EXPORT_SIZE_MB = 50

# Excel export settings
EXCEL_ENGINE = "openpyxl"  # or "xlsxwriter"
EXCEL_INCLUDE_INDEX = False
EXCEL_FREEZE_HEADER = True

# PDF export settings
PDF_PAGE_SIZE = "A4"  # or "Letter"
PDF_ORIENTATION = "portrait"  # or "landscape"
PDF_FONT_SIZE = 10

# ============================================================================
# ANALYSIS TOOL SETTINGS
# ============================================================================

# Forecasting
ENABLE_FORECASTING = False  # Phase 2
FORECASTING_METHODS = ["arima", "prophet", "linear", "exponential"]
DEFAULT_FORECAST_PERIODS = 12
FORECAST_CONFIDENCE_INTERVAL = 0.95

# What-If Analysis
ENABLE_WHAT_IF = False  # Phase 2
WHAT_IF_MAX_SCENARIOS = 10
WHAT_IF_MAX_VARIABLES = 5

# Root Cause Analysis
ENABLE_ROOT_CAUSE = False  # Phase 2
ROOT_CAUSE_MIN_CORRELATION = 0.5
ROOT_CAUSE_MAX_FACTORS = 10

# Anomaly Detection
ENABLE_ANOMALY_DETECTION = False  # Phase 2
ANOMALY_METHOD = "isolation_forest"  # or "local_outlier_factor", "one_class_svm"
ANOMALY_CONTAMINATION = 0.1  # Expected proportion of outliers

# ============================================================================
# SAFETY & SECURITY SETTINGS
# ============================================================================

# Rate limiting
TOOL_RATE_LIMIT = 100  # Requests per minute
TOOL_RATE_LIMIT_WINDOW = 60  # seconds

# Timeouts
DEFAULT_TOOL_TIMEOUT = 60  # seconds
MAX_TOOL_TIMEOUT = 300  # seconds

# Confirmation required for potentially destructive operations
REQUIRE_CONFIRMATION = {
    "python_repl": True,  # Code execution needs confirmation
    "data_transformer": False,  # Data operations are safe (no write to original)
    "export": False  # Export is safe
}

# Tool execution limits
MAX_CONCURRENT_TOOLS = 5  # Max tools running simultaneously
TOOL_RETRY_ATTEMPTS = 3
TOOL_RETRY_DELAY = 1  # seconds

# ============================================================================
# LOGGING & MONITORING
# ============================================================================

# Tool usage logging
LOG_TOOL_USAGE = True
LOG_TOOL_EXECUTION_TIME = True
LOG_TOOL_ERRORS = True

# Performance monitoring
MONITOR_TOOL_PERFORMANCE = True
PERFORMANCE_THRESHOLD_SECONDS = 5  # Warn if tool takes longer

# ============================================================================
# TOOL-SPECIFIC SETTINGS
# ============================================================================

# RAG Retrieval Tool
RAG_RETRIEVAL_SETTINGS = {
    "default_top_k": 3,
    "include_metadata": True,
    "combine_results": True
}

# Chart Generator Tool
CHART_GENERATOR_SETTINGS = {
    "auto_detect_type": True,  # Auto-detect best chart type
    "interactive": True,  # Make charts interactive
    "show_legend": True,
    "show_grid": True
}

# Data Transformer Tool
DATA_TRANSFORMER_SETTINGS = {
    "create_copy": True,  # Always work on a copy
    "validate_result": True,  # Validate after transformation
    "show_preview": True  # Show preview of result
}

# Export Tool
EXPORT_TOOL_SETTINGS = {
    "auto_timestamp": True,  # Add timestamp to filename
    "compress_large_files": True,  # Compress files > 10MB
    "include_metadata": True  # Include analysis metadata
}

# ============================================================================
# VALIDATION
# ============================================================================

def validate_tool_config():
    """Validate tool configuration"""
    errors = []
    
    # Check paths
    if not EXPORT_DIR.exists():
        errors.append(f"Export directory does not exist: {EXPORT_DIR}")
    
    # Check settings
    if CODE_EXECUTION_TIMEOUT < 1:
        errors.append("CODE_EXECUTION_TIMEOUT must be >= 1")
    
    if TOOL_RATE_LIMIT < 1:
        errors.append("TOOL_RATE_LIMIT must be >= 1")
    
    if not EXPORT_FORMATS:
        errors.append("At least one export format must be enabled")
    
    return errors

# Run validation
_errors = validate_tool_config()
if _errors:
    print("⚠️ Tool Configuration Warnings:")
    for error in _errors:
        print(f"  - {error}")
