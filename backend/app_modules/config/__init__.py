"""
Vishleshak AI Configuration Package
Exports all configuration modules
"""

from .settings import (
    GROQ_API_KEY,
    LLM_MODEL,
    CHAT_MODEL,
    LLM_TEMPERATURE,
    CHAT_TEMPERATURE,
    MAX_TOKENS,
    CHAT_MEMORY_WINDOW,
    CHAT_HISTORY_DB,
    UPLOAD_FOLDER,
    OUTPUT_FOLDER,
    MAX_FILE_SIZE_MB,
    SUPPORTED_FORMATS,
    CONFIDENCE_THRESHOLD,
    CORRELATION_THRESHOLD,
    OUTLIER_THRESHOLD,
    ENABLE_CORRELATION_ANALYSIS,
    ENABLE_OUTLIER_DETECTION,
    ENABLE_PATTERN_RECOGNITION,
    ENABLE_FORECASTING,
    ENABLE_CLUSTERING,
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    LOG_LEVEL,
    LOG_FILE,
    MIN_SAMPLES_FOR_NORMALITY_TEST,
    MIN_SAMPLES_FOR_CLUSTERING,
    MAX_CLUSTERS,
    TREND_SIGNIFICANCE_LEVEL,
    MINIMUM_CYCLE_COUNT,
    ANOMALY_THRESHOLD_SIGMA,
    HIGH_MISSING_THRESHOLD,
    LOW_VARIANCE_CV_THRESHOLD,
    DUPLICATE_WARNING_THRESHOLD,
    validate_settings,
)

try:
    from .agent_config import (
        AGENT_TYPE,
        MAX_ITERATIONS,
        MAX_EXECUTION_TIME,
        AGENT_TEMPERATURE,
        VERBOSE,
        SMART_TOOL_SELECTION,
        MAX_TOOLS_PER_QUERY,
        TOOL_SELECTION_STRATEGY,
        TRACK_TOOL_PERFORMANCE,
        ENABLE_REFLECTION,
        MIN_CONFIDENCE_THRESHOLD,
        MAX_REFLECTION_RETRIES,
        STORE_TOOL_HISTORY,
        MAX_TOOL_HISTORY,
        ENABLE_TOOL_LEARNING,
        ENABLE_PLANNING,
    )
except Exception:
    pass

try:
    from .memory_config import (
        ENABLE_SHORT_TERM_MEMORY,
        SHORT_TERM_WINDOW,
        ENABLE_WORKING_MEMORY,
        WORKING_MEMORY_WINDOW,
        WORKING_MEMORY_UPDATE_FREQUENCY,
        ENABLE_LONG_TERM_MEMORY,
        ENABLE_SEMANTIC_MEMORY,
        ENABLE_EPISODIC_MEMORY,
    )
except Exception:
    pass

try:
    from .chain_config import (
        QA_WITH_RAG_PROMPT,
        QA_SIMPLE_PROMPT,
    )
except Exception:
    pass

try:
    from .tool_config import (
        TOOL_PROMPT_TEMPLATE,
    )
except Exception:
    pass

try:
    from .domain_config import (
        get_domain_config,
        detect_domain_from_columns,
        get_domain_system_prompt,
        get_domain_colors,
        get_domain_focus_areas,
        get_domain_intelligence,
    )
except Exception:
    pass