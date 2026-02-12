"""
FINBOT Configuration Settings
Centralized configuration for the entire application
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = DATA_DIR / "memory"
UPLOADS_DIR = DATA_DIR / "uploads"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# Create directories
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast and efficient
GROQ_TEMPERATURE = 0.3

# Memory Configuration
MEMORY_WINDOW_SIZE = 5  # Number of recent messages to remember
MAX_HISTORY_LENGTH = 50  # Maximum conversation history
SUMMARY_INTERVAL = 10  # Summarize every N messages

# RAG Configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 3

# Analysis Configuration
CONFIDENCE_THRESHOLD = 0.6
MAX_FILE_SIZE_MB = 10

# Streamlit Configuration
PAGE_TITLE = "💰 FINBOT - AI Financial Assistant"
PAGE_ICON = "💼"
LAYOUT = "wide"
