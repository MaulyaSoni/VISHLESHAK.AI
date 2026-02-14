"""
RAG System Configuration for FINBOT v4
Handles all RAG-related settings and configurations
"""
import os
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================

# Base paths
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"

# Vector database paths
VECTOR_DB_PATH = STORAGE_DIR / "vector_db"
VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)

# ============================================================================
# VECTOR STORE SETTINGS
# ============================================================================

# Collection names for different use cases
VECTOR_DB_COLLECTIONS = {
    "analyses": "analysis_history",      # RAG Use Case 1: Historical memory
    "knowledge": "domain_knowledge",     # RAG Use Case 2: Knowledge base
    "patterns": "pattern_library",       # RAG Use Case 3: Pattern matching
    "documents": "document_store"        # RAG Use Case 4: Document Q&A
}

# ChromaDB settings
CHROMA_SETTINGS = {
    "anonymized_telemetry": False,
    "allow_reset": True,
    "is_persistent": True
}

# ============================================================================
# EMBEDDING SETTINGS
# ============================================================================

# Embedding model configuration
# Using HuggingFace sentence-transformers (FREE, local, no API needed)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE = 32
EMBEDDING_DEVICE = "cpu"  # Change to "cuda" if GPU available

# Cache settings
CACHE_EMBEDDINGS = True
CACHE_DIR = STORAGE_DIR / "cache" / "embeddings"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_SIZE_LIMIT_MB = 500  # Max cache size in megabytes

# ============================================================================
# RETRIEVAL SETTINGS
# ============================================================================

# Default retrieval parameters
DEFAULT_TOP_K = 3  # Number of results to retrieve
DEFAULT_TOP_K_ANALYSES = 2  # For historical analyses
DEFAULT_TOP_K_KNOWLEDGE = 3  # For knowledge base
DEFAULT_TOP_K_PATTERNS = 3  # For pattern matching
DEFAULT_TOP_K_DOCUMENTS = 5  # For documents

# Similarity thresholds
SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score (0-1)
HIGH_SIMILARITY_THRESHOLD = 0.85  # For high-confidence matches

# Context limits
MAX_CONTEXT_LENGTH = 4000  # Max characters in retrieved context
MAX_CONTEXT_TOKENS = 1000  # Max tokens (approximate)

# ============================================================================
# KNOWLEDGE BASE SETTINGS
# ============================================================================

# Knowledge base paths
KNOWLEDGE_BASE_DOMAINS = {
    "education": KNOWLEDGE_BASE_DIR / "education",
    "finance": KNOWLEDGE_BASE_DIR / "finance",
    "general": KNOWLEDGE_BASE_DIR / "general"
}

# Create knowledge base directories
for domain_path in KNOWLEDGE_BASE_DOMAINS.values():
    domain_path.mkdir(parents=True, exist_ok=True)

# Auto-load knowledge base on startup
AUTO_LOAD_KNOWLEDGE = True
KNOWLEDGE_FILE_EXTENSIONS = [".txt", ".md", ".pdf", ".docx"]

# ============================================================================
# DOCUMENT PROCESSING
# ============================================================================

# Text splitting configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
TEXT_SPLITTER_TYPE = "recursive"  # or "character", "token"

# Supported document formats
SUPPORTED_DOC_FORMATS = {
    ".txt": "text",
    ".md": "markdown",
    ".pdf": "pdf",
    ".docx": "docx",
    ".csv": "csv",
    ".json": "json"
}

# ============================================================================
# RAG USE CASE TOGGLES
# ============================================================================

# Enable/disable specific RAG use cases
ENABLE_HISTORICAL_MEMORY = True    # Use Case 1: Remember past analyses
ENABLE_KNOWLEDGE_BASE = True        # Use Case 2: Query domain knowledge
ENABLE_PATTERN_MATCHING = True      # Use Case 3: Find similar patterns
ENABLE_DOCUMENT_QA = True           # Use Case 4: Answer from documents

# ============================================================================
# ANALYSIS STORAGE
# ============================================================================

# What to store from each analysis
STORE_ANALYSIS_FIELDS = [
    "insights",
    "key_findings",
    "recommendations",
    "statistical_summary",
    "patterns_detected",
    "correlations",
    "outliers"
]

# Metadata to include
ANALYSIS_METADATA_FIELDS = [
    "timestamp",
    "dataset_name",
    "num_rows",
    "num_columns",
    "analysis_type",
    "session_id"
]

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Batch processing
BATCH_SIZE_DOCUMENTS = 10  # Documents to process at once
BATCH_SIZE_QUERIES = 5  # Queries to process at once

# Timeouts
EMBEDDING_TIMEOUT = 30  # Seconds
RETRIEVAL_TIMEOUT = 10  # Seconds

# ============================================================================
# LOGGING
# ============================================================================

# RAG operation logging
LOG_RAG_OPERATIONS = True
LOG_RETRIEVAL_RESULTS = True
LOG_EMBEDDING_STATS = True

# ============================================================================
# VALIDATION
# ============================================================================

def validate_rag_config():
    """Validate RAG configuration"""
    errors = []
    
    # Check paths exist
    if not VECTOR_DB_PATH.exists():
        errors.append(f"Vector DB path does not exist: {VECTOR_DB_PATH}")
    
    if not KNOWLEDGE_BASE_DIR.exists():
        errors.append(f"Knowledge base path does not exist: {KNOWLEDGE_BASE_DIR}")
    
    # Check settings
    if DEFAULT_TOP_K < 1:
        errors.append("DEFAULT_TOP_K must be >= 1")
    
    if not 0 <= SIMILARITY_THRESHOLD <= 1:
        errors.append("SIMILARITY_THRESHOLD must be between 0 and 1")
    
    if CHUNK_SIZE < 100:
        errors.append("CHUNK_SIZE too small, should be >= 100")
    
    return errors

# Run validation
_errors = validate_rag_config()
if _errors:
    print("⚠️ RAG Configuration Warnings:")
    for error in _errors:
        print(f"  - {error}")
