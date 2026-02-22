"""
Sequential Chain Configuration for Vishleshak AI v1
Settings for multi-step reasoning and chain-of-thought
"""

from pathlib import Path

# ============================================================================
# SEQUENTIAL CHAIN SETTINGS
# ============================================================================

# Chain types available
CHAIN_TYPES = {
    "simple": "Single-step direct reasoning",
    "sequential": "Multi-step sequential reasoning",
    "decomposition": "Question decomposition then answer",
    "chain_of_thought": "Explicit step-by-step reasoning",
    "memory_augmented": "Reasoning with memory at each step"
}

# Default chain type
DEFAULT_CHAIN_TYPE = "memory_augmented"

# ============================================================================
# QUESTION DECOMPOSITION
# ============================================================================

# Enable automatic question decomposition
ENABLE_DECOMPOSITION = True

# Complexity threshold for decomposition
DECOMPOSITION_THRESHOLD = 0.7  # 0-1, higher = more complex needed

# Maximum sub-questions
MAX_SUB_QUESTIONS = 5

# Decomposition strategy
DECOMPOSITION_STRATEGY = "smart"  # "simple", "smart", "llm"

# Keywords indicating complex questions
COMPLEX_QUESTION_INDICATORS = [
    'and', 'also', 'plus', 'additionally', 'furthermore',
    'compare', 'contrast', 'difference', 'relationship',
    'how does', 'what if', 'why', 'explain',
    'analyze', 'evaluate', 'assess', 'determine',
    'multiple', 'several', 'various', 'both'
]

# ============================================================================
# CHAIN OF THOUGHT SETTINGS
# ============================================================================

# Enable chain-of-thought reasoning
ENABLE_CHAIN_OF_THOUGHT = True

# Show reasoning steps to user
SHOW_REASONING_STEPS = True  # Set False to hide internal reasoning

# Reasoning step types
REASONING_STEPS = [
    "understand",    # Understand the question
    "decompose",     # Break into sub-questions
    "retrieve",      # Retrieve relevant context
    "reason",        # Perform reasoning
    "validate",      # Validate conclusions
    "synthesize"     # Synthesize final answer
]

# Minimum reasoning steps
MIN_REASONING_STEPS = 3

# Maximum reasoning steps
MAX_REASONING_STEPS = 6

# ============================================================================
# MEMORY INTEGRATION
# ============================================================================

# Use memory at each reasoning step
MEMORY_AT_EACH_STEP = True

# Memory retrieval strategy per step
STEP_MEMORY_STRATEGY = {
    "understand": "short_term",      # Use recent context
    "decompose": "semantic",         # Use facts/preferences
    "retrieve": "all",               # Use all memory tiers
    "reason": "relevant",            # Use relevant context
    "validate": "episodic",          # Use past similar situations
    "synthesize": "all"              # Use comprehensive context
}

# ============================================================================
# REASONING VALIDATION
# ============================================================================

# Enable reasoning validation
ENABLE_VALIDATION = True

# Validation checks
VALIDATION_CHECKS = [
    "consistency",      # Check logical consistency
    "completeness",     # Check if question fully answered
    "accuracy",         # Check against known facts
    "relevance"         # Check relevance to question
]

# Confidence threshold for validation
VALIDATION_CONFIDENCE_THRESHOLD = 0.7

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Maximum time per chain execution (seconds)
CHAIN_TIMEOUT = 60

# Enable parallel step execution (where possible)
ENABLE_PARALLEL_STEPS = False  # Set True for faster execution

# Cache intermediate results
CACHE_INTERMEDIATE_RESULTS = True
CACHE_TTL_SECONDS = 300  # 5 minutes

# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

# Show detailed prompts in logs
LOG_PROMPTS = False  # Set True for debugging

# Prompt style
PROMPT_STYLE = "conversational"  # "conversational", "formal", "technical"

# ============================================================================
# ERROR HANDLING
# ============================================================================

# Retry failed steps
ENABLE_RETRY = True
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 1

# Fallback to simple chain on error
FALLBACK_TO_SIMPLE = True

# ============================================================================
# LOGGING
# ============================================================================

LOG_CHAIN_EXECUTION = True
LOG_REASONING_STEPS = True
LOG_MEMORY_RETRIEVAL = True
LOG_VALIDATION_RESULTS = True

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Enable/disable major features
ENABLE_SEQUENTIAL_CHAINS = True
ENABLE_QUESTION_DECOMPOSITION = True
ENABLE_COT_REASONING = True
ENABLE_MEMORY_AUGMENTATION = True
ENABLE_REASONING_VALIDATION = True

# ============================================================================
# VALIDATION
# ============================================================================

def validate_chain_config():
    """Validate chain configuration"""
    errors = []
    
    if MAX_SUB_QUESTIONS < 1:
        errors.append("MAX_SUB_QUESTIONS must be >= 1")
    
    if not 0 <= DECOMPOSITION_THRESHOLD <= 1:
        errors.append("DECOMPOSITION_THRESHOLD must be between 0 and 1")
    
    if CHAIN_TIMEOUT < 10:
        errors.append("CHAIN_TIMEOUT too small, should be >= 10 seconds")
    
    return errors

# Run validation
_errors = validate_chain_config()
if _errors:
    print("⚠️ Chain Configuration Warnings:")
    for error in _errors:
        print(f"  - {error}")
