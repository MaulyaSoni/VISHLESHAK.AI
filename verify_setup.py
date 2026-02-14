"""
Quick verification script for FINBOT v4
Tests all critical imports and basic functionality
"""

import sys
print("=" * 60)
print("FINBOT v4 - Verify Setup")
print("=" * 60)

# Test 1: Config
try:
    from config import settings
    print("[OK] Config loaded successfully")
    print(f"   - Model: {settings.LLM_MODEL}")
    print(f"   - Memory window: {settings.CHAT_MEMORY_WINDOW}")
except Exception as e:
    print(f"[ERROR] Config error: {e}")
    sys.exit(1)

# Test 2: Core modules
try:
    from core.llm import get_analysis_llm, get_chat_llm
    print("[OK] Core LLM module loaded")
except Exception as e:
    print(f"[ERROR] Core LLM error: {e}")
    sys.exit(1)

try:
    from core.memory import ChatMemoryManager, ConversationManager
    print("[OK] Core Memory module loaded (SQLite-based)")
except Exception as e:
    print(f"[ERROR] Core Memory error: {e}")
    sys.exit(1)

# Test 3: Utils
try:
    from utils.data_loader import DataLoader
    print("[OK] Data Loader module loaded")
except Exception as e:
    print(f"[ERROR] Data Loader error: {e}")
    sys.exit(1)

# Test 4: Analyzers
try:
    from analyzers.statistical_analyzer import StatisticalAnalyzer
    from analyzers.pattern_detector import PatternDetector
    from analyzers.insight_generator import InsightGenerator
    print("[OK] All analyzer modules loaded")
    print("   - Statistical Analyzer (20+ metrics)")
    print("   - Pattern Detector (6 types)")
    print("   - Insight Generator (AI-powered)")
except Exception as e:
    print(f"[ERROR] Analyzers error: {e}")
    sys.exit(1)

# Test 5: Chatbot & RAG
try:
    from chatbot.qa_chain import DataContextManager, EnhancedQAChain
    from rag.retriever import SmartRetriever
    from tools.tool_registry import ToolRegistry
    print("[OK] Chatbot Q&A & RAG modules loaded")
    print("   - EnhancedQAChain (RAG + Tools)")
    print("   - SmartRetriever")
    print("   - ToolRegistry")
except Exception as e:
    print(f"[ERROR] Chatbot/RAG error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Test memory functionality
try:
    import tempfile
    import os
    
    import uuid
    # Create temp db for testing
    temp_db = os.path.join(tempfile.gettempdir(), f"test_finbot_{uuid.uuid4().hex}.db")
    
    # Test memory manager
    memory_mgr = ChatMemoryManager(db_path=temp_db)
    memory_mgr.create_session("test_session_123")
    memory_mgr.add_message("test_session_123", "human", "Test question")
    memory_mgr.add_message("test_session_123", "ai", "Test answer")
    
    # Retrieve messages
    messages = memory_mgr.get_messages("test_session_123")
    assert len(messages) == 2, "Should have 2 messages"
    assert messages[0]['type'] == 'human', "First should be human"
    assert messages[1]['type'] == 'ai', "Second should be AI"
    
    # Clean up
    memory_mgr = None # Release handle
    try:
        if os.path.exists(temp_db):
            os.remove(temp_db)
    except PermissionError:
        pass # Ignore file lock on cleanup
    
    print("[OK] Memory persistence test passed")
    print("   - SQLite database working")
    print("   - Message storage/retrieval working")
except Exception as e:
    print(f"[ERROR] Memory test error: {e}")
    sys.exit(1)

# Test 7: Check if .env exists
import os
if os.path.exists('.env'):
    print("[OK] .env file found")
    # Check if API key is set
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here":
        print("   - [OK] GROQ_API_KEY is configured")
    else:
        print("   - [WARN] GROQ_API_KEY not configured (add it to .env)")
else:
    print("[WARN] .env file not found - create from .env.example")

print("=" * 60)
print("[SUCCESS] All core modules verified successfully!")
print("=" * 60)
print()
print("Next steps:")
print("1. Add your Groq API key to .env file")
print("2. Run: streamlit run app.py")
