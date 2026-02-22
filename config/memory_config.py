"""
Memory System Configuration for Vishleshak AI v1
Comprehensive settings for multi-tiered memory system
"""

from pathlib import Path
from datetime import timedelta

# ============================================================================
# PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
MEMORY_DB_DIR = STORAGE_DIR / "memory_db"
MEMORY_DB_DIR.mkdir(parents=True, exist_ok=True)

# Database files
MEMORY_DB_PATH = MEMORY_DB_DIR / "enhanced_memory.db"
SCHEMA_PATH = STORAGE_DIR / "schema" / "enhanced_schema.sql"

# ============================================================================
# MEMORY TIER SETTINGS
# ============================================================================

# SHORT-TERM MEMORY (Buffer)
SHORT_TERM_WINDOW = 10  # Last N messages
SHORT_TERM_MAX_TOKENS = 2000  # Maximum tokens in short-term

# WORKING MEMORY (Summary)
WORKING_MEMORY_WINDOW = 50  # Messages to summarize
WORKING_MEMORY_UPDATE_FREQUENCY = 10  # Update every N messages
WORKING_MEMORY_MAX_TOKENS = 500  # Maximum summary tokens
COMPRESSION_TARGET_RATIO = 0.3  # Target 30% of original size

# LONG-TERM MEMORY (Vector DB)
LONG_TERM_RETRIEVAL_K = 5  # Retrieve top K relevant memories
LONG_TERM_SIMILARITY_THRESHOLD = 0.7  # Minimum similarity
LONG_TERM_MAX_AGE_DAYS = 365  # Keep memories for 1 year

# SEMANTIC MEMORY
SEMANTIC_CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence to use
SEMANTIC_MAX_FACTS_PER_USER = 1000  # Limit facts per user
SEMANTIC_VALIDATION_FREQUENCY = timedelta(days=30)  # Revalidate monthly

# EPISODIC MEMORY
EPISODIC_IMPORTANCE_THRESHOLD = 0.8  # Minimum to save as episode
EPISODIC_MAX_PER_USER = 100  # Maximum episodes per user
EPISODIC_RETRIEVAL_K = 3  # Retrieve top K episodes

# ============================================================================
# IMPORTANCE SCORING (LSTM-like)
# ============================================================================

# Base importance factors
IMPORTANCE_FACTORS = {
    "message_length": 0.15,      # Longer messages = more important
    "keyword_presence": 0.25,    # Specific keywords boost importance
    "question_depth": 0.20,      # Complex questions = more important
    "user_feedback": 0.25,       # Positive feedback boosts
    "temporal_recency": 0.15     # Recent = more important
}

# Important keywords (boost importance)
IMPORTANT_KEYWORDS = [
    'important', 'remember', 'always', 'never', 'prefer', 'like', 'dislike',
    'key', 'critical', 'essential', 'must', 'should', 'favorite',
    'breakthrough', 'insight', 'discovery', 'found', 'realized'
]

# Message length thresholds
LENGTH_THRESHOLDS = {
    "short": 50,     # < 50 chars = short
    "medium": 150,   # 50-150 = medium
    "long": 150      # > 150 = long (higher importance)
}

# ============================================================================
# DECAY AND FORGETTING (LSTM-like)
# ============================================================================

# Decay settings
ENABLE_MEMORY_DECAY = True
DECAY_RATE = 0.99  # Multiply decay_factor by this per day
DECAY_UPDATE_FREQUENCY = timedelta(days=1)  # Update daily

# Forgetting thresholds
FORGETTING_ENABLED = True
FORGETTING_THRESHOLD = 0.2  # Delete if effective_importance < 0.2
FORGETTING_MIN_AGE_DAYS = 30  # Don't delete memories < 30 days old
FORGETTING_PRESERVE_EPISODES = True  # Never delete episodic memories

# Access-based reinforcement
ACCESS_BOOST_FACTOR = 0.1  # Boost importance by 10% per access
MAX_ACCESS_BOOST = 0.5  # Maximum boost from accesses

# ============================================================================
# CONSOLIDATION SETTINGS
# ============================================================================

# When to consolidate (like sleep in brain)
CONSOLIDATION_ENABLED = True
CONSOLIDATION_FREQUENCY = timedelta(hours=24)  # Daily consolidation
CONSOLIDATION_MESSAGE_THRESHOLD = 100  # Consolidate after 100 messages

# What to consolidate
CONSOLIDATE_SUMMARIES = True  # Create/update summaries
CONSOLIDATE_SEMANTIC = True   # Extract semantic memories
CONSOLIDATE_CLEANUP = True    # Remove low-importance memories

# ============================================================================
# CONTEXT RETRIEVAL STRATEGY
# ============================================================================

# Context assembly strategy
CONTEXT_STRATEGY = "hybrid"  # 'aggressive', 'conservative', 'hybrid'

# Strategies defined
CONTEXT_STRATEGIES = {
    "aggressive": {
        "short_term": 20,
        "working_memory": True,
        "long_term_k": 10,
        "semantic_k": 5,
        "episodic_k": 5
    },
    "conservative": {
        "short_term": 10,
        "working_memory": True,
        "long_term_k": 5,
        "semantic_k": 3,
        "episodic_k": 2
    },
    "hybrid": {
        "short_term": 15,
        "working_memory": True,
        "long_term_k": 7,
        "semantic_k": 4,
        "episodic_k": 3
    }
}

# Current strategy
CURRENT_STRATEGY = CONTEXT_STRATEGIES[CONTEXT_STRATEGY]

# Context window limits
MAX_CONTEXT_TOKENS = 4000  # Maximum total context tokens
MAX_CONTEXT_CHARS = 16000  # Maximum total context characters

# ============================================================================
# TOPIC DETECTION
# ============================================================================

# Topic detection settings
ENABLE_TOPIC_DETECTION = True
TOPIC_DETECTION_METHOD = "keyword"  # 'keyword', 'embedding', 'llm'

# Predefined topics
PREDEFINED_TOPICS = [
    "data_analysis", "statistics", "visualization", "export",
    "troubleshooting", "general_question", "feedback", "preferences"
]

# ============================================================================
# SEMANTIC EXTRACTION
# ============================================================================

# What to extract as semantic memories
EXTRACT_USER_PREFERENCES = True
EXTRACT_FACTS = True
EXTRACT_INSIGHTS = True
EXTRACT_RULES = True

# Extraction confidence thresholds
MIN_EXTRACTION_CONFIDENCE = 0.6
REQUIRE_MULTIPLE_EVIDENCE = True  # Need 2+ confirmations

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Batch processing
BATCH_SIZE_MESSAGES = 50
BATCH_SIZE_EMBEDDINGS = 32

# Timeouts
MEMORY_OPERATION_TIMEOUT = 30  # seconds
CONSOLIDATION_TIMEOUT = 300     # seconds

# Caching
CACHE_RETRIEVAL_RESULTS = True
CACHE_TTL_SECONDS = 300  # 5 minutes

# ============================================================================
# LOGGING
# ============================================================================

LOG_MEMORY_OPERATIONS = True
LOG_IMPORTANCE_CALCULATIONS = False  # Verbose, disable in production
LOG_RETRIEVAL_RESULTS = True
LOG_CONSOLIDATION = True

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Enable/disable major features
ENABLE_SHORT_TERM_MEMORY = True
ENABLE_WORKING_MEMORY = True
ENABLE_LONG_TERM_MEMORY = True
ENABLE_SEMANTIC_MEMORY = True
ENABLE_EPISODIC_MEMORY = True

# Advanced features
ENABLE_IMPORTANCE_SCORING = True
ENABLE_DECAY_MECHANISM = True
ENABLE_AUTOMATIC_CONSOLIDATION = True
ENABLE_SMART_FORGETTING = True

# ============================================================================
# USER SETTINGS
# ============================================================================

# Default user ID for single-user mode
DEFAULT_USER_ID = "default_user"

# Multi-user support
MULTI_USER_MODE = False  # Enable for multi-user deployments

# ============================================================================
# VALIDATION
# ============================================================================

def validate_memory_config():
    """Validate memory configuration"""
    errors = []
    
    if SHORT_TERM_WINDOW < 1:
        errors.append("SHORT_TERM_WINDOW must be >= 1")
    
    if not 0 < DECAY_RATE <= 1:
        errors.append("DECAY_RATE must be between 0 and 1")
    
    if FORGETTING_THRESHOLD < 0:
        errors.append("FORGETTING_THRESHOLD must be >= 0")
    
    if MAX_CONTEXT_TOKENS < 1000:
        errors.append("MAX_CONTEXT_TOKENS too small, should be >= 1000")
    
    return errors

# Run validation
_errors = validate_memory_config()
if _errors:
    print("⚠️ Memory Configuration Warnings:")
    for error in _errors:
        print(f"  - {error}")
