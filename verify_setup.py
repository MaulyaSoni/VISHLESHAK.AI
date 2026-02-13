"""
Quick verification script for FINBOT v4
Tests all critical imports and basic functionality
"""

import sys
print("=" * 60)
print("FINBOT v4 - Import Verification")
print("=" * 60)

# Test 1: Config
try:
    from config import settings
    print("✅ Config loaded successfully")
    print(f"   - Model: {settings.LLM_MODEL}")
    print(f"   - Memory window: {settings.CHAT_MEMORY_WINDOW}")
except Exception as e:
    print(f"❌ Config error: {e}")
    sys.exit(1)

# Test 2: Core modules
try:
    from core.llm import get_analysis_llm, get_chat_llm
    print("✅ Core LLM module loaded")
except Exception as e:
    print(f"❌ Core LLM error: {e}")
    sys.exit(1)

try:
    from core.memory import ChatMemoryManager, ConversationManager
    print("✅ Core Memory module loaded (SQLite-based)")
except Exception as e:
    print(f"❌ Core Memory error: {e}")
    sys.exit(1)

# Test 3: Utils
try:
    from utils.data_loader import DataLoader
    print("✅ Data Loader module loaded")
except Exception as e:
    print(f"❌ Data Loader error: {e}")
    sys.exit(1)

# Test 4: Analyzers
try:
    from analyzers.statistical_analyzer import StatisticalAnalyzer
    from analyzers.pattern_detector import PatternDetector
    from analyzers.insight_generator import InsightGenerator
    print("✅ All analyzer modules loaded")
    print("   - Statistical Analyzer (20+ metrics)")
    print("   - Pattern Detector (6 types)")
    print("   - Insight Generator (AI-powered)")
except Exception as e:
    print(f"❌ Analyzers error: {e}")
    sys.exit(1)

# Test 5: Chatbot
try:
    from chatbot.qa_chain import DataContextManager, DataQAChain
    print("✅ Chatbot Q&A module loaded")
except Exception as e:
    print(f"❌ Chatbot error: {e}")
    sys.exit(1)

# Test 6: Test memory functionality
try:
    import tempfile
    import os
    
    # Create temp db for testing
    temp_db = os.path.join(tempfile.gettempdir(), "test_finbot.db")
    
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
    if os.path.exists(temp_db):
        os.remove(temp_db)
    
    print("✅ Memory persistence test passed")
    print("   - SQLite database working")
    print("   - Message storage/retrieval working")
except Exception as e:
    print(f"❌ Memory test error: {e}")
    sys.exit(1)

# Test 7: Check if .env exists
import os
if os.path.exists('.env'):
    print("✅ .env file found")
    # Check if API key is set
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here":
        print("   - ✅ GROQ_API_KEY is configured")
    else:
        print("   - ⚠️  GROQ_API_KEY not configured (add it to .env)")
else:
    print("⚠️  .env file not found - create from .env.example")

print("=" * 60)
print("🎉 All core modules verified successfully!")
print("=" * 60)
print()
print("Next steps:")
print("1. Add your Groq API key to .env file")
print("2. Run: streamlit run app.py")
print()
print("Get free API key: https://console.groq.com/keys")
