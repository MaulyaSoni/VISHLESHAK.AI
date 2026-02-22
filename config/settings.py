"""
Configuration Settings for Vishleshak AI v1
All application settings in one centralized location
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Groq API Key (Get free key from: https://console.groq.com/keys)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Model Selection
# Updated to use currently supported models (llama-3.1-70b-versatile was decommissioned)
# Options: "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"
LLM_MODEL = "llama-3.3-70b-versatile"  # Best model for deep analysis
CHAT_MODEL = "llama-3.3-70b-versatile"  # Best model for Q&A

# LLM Parameters
LLM_TEMPERATURE = 0.1  # Lower = more deterministic (0-1)
CHAT_TEMPERATURE = 0.3  # Slightly higher for conversational responses
MAX_TOKENS = 8192  # Maximum response length

# ============================================================================
# CHAT MEMORY CONFIGURATION
# ============================================================================

# Chat history settings
CHAT_MEMORY_WINDOW = 10  # Number of messages to remember
CHAT_HISTORY_DB = "data/memory/conversations.db"  # SQLite database path

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

# File storage paths
UPLOAD_FOLDER = "data/uploads/"  # Temporary file storage
OUTPUT_FOLDER = "data/outputs/"  # Analysis outputs (if needed)

# ============================================================================
# DATA ANALYSIS CONFIGURATION
# ============================================================================

# File upload limits
MAX_FILE_SIZE_MB = 50  # Maximum file size in megabytes
SUPPORTED_FORMATS = ['.csv', '.xlsx', '.xls']  # Supported file formats

# Analysis thresholds
CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for analysis
CORRELATION_THRESHOLD = 0.5  # Minimum for "strong" correlation
OUTLIER_THRESHOLD = 1.5  # IQR multiplier for outlier detection

# Feature toggles
ENABLE_CORRELATION_ANALYSIS = True
ENABLE_OUTLIER_DETECTION = True
ENABLE_PATTERN_RECOGNITION = True
ENABLE_FORECASTING = True
ENABLE_CLUSTERING = True

# ============================================================================
# UI CONFIGURATION
# ============================================================================

# Page settings
PAGE_TITLE = "🤖 Vishleshak AI v1 - Advanced Data Intelligence"
PAGE_ICON = "🤖"
LAYOUT = "wide"  # "centered" or "wide"

# ============================================================================
# LOGGING CONFIGURATION (Optional)
# ============================================================================

# Logging settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "logs/Vishleshak AI v1.log"  # Log file path

# ============================================================================
# ADVANCED SETTINGS (Don't modify unless you know what you're doing)
# ============================================================================

# Statistical analysis settings
MIN_SAMPLES_FOR_NORMALITY_TEST = 8  # Minimum samples for Shapiro-Wilk test
MIN_SAMPLES_FOR_CLUSTERING = 10  # Minimum samples for K-means
MAX_CLUSTERS = 5  # Maximum number of clusters for K-means

# Pattern detection settings
TREND_SIGNIFICANCE_LEVEL = 0.05  # p-value threshold for trend significance
MINIMUM_CYCLE_COUNT = 3  # Minimum cycles to detect cyclical pattern
ANOMALY_THRESHOLD_SIGMA = 3  # Standard deviations for anomaly detection

# Data quality thresholds
HIGH_MISSING_THRESHOLD = 0.3  # 30% missing = high concern
LOW_VARIANCE_CV_THRESHOLD = 1  # Coefficient of variation < 1% = low variance
DUPLICATE_WARNING_THRESHOLD = 0.05  # 5% duplicates = warning

# ============================================================================
# VALIDATION
# ============================================================================

def validate_settings():
    """Validate that all required settings are properly configured"""
    errors = []
    
    # Check API key
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY not set in environment variables")
    
    # Check file size
    if MAX_FILE_SIZE_MB <= 0:
        errors.append("MAX_FILE_SIZE_MB must be positive")
    
    # Check thresholds
    if not (0 <= CORRELATION_THRESHOLD <= 1):
        errors.append("CORRELATION_THRESHOLD must be between 0 and 1")
    
    if OUTLIER_THRESHOLD <= 0:
        errors.append("OUTLIER_THRESHOLD must be positive")
    
    return errors

# Run validation on import
_validation_errors = validate_settings()
if _validation_errors:
    print("⚠️ Configuration Warnings:")
    for error in _validation_errors:
        print(f"  - {error}")
