"""Test script to verify all imports work"""

print("Testing FINBOT v4 imports...")
print("-" * 50)

try:
    print("1. Testing config...")
    from config import settings
    print("   ✅ Config imported successfully")
except Exception as e:
    print(f"   ❌ Config error: {e}")
    exit(1)

try:
    print("2. Testing core.llm...")
    from core.llm import get_analysis_llm, get_chat_llm
    print("   ✅ Core LLM imported successfully")
except Exception as e:
    print(f"   ❌ Core LLM error: {e}")
    exit(1)

try:
    print("3. Testing core.memory...")
    from core.memory import ChatMemoryManager
    print("   ✅ Core Memory imported successfully")
except Exception as e:
    print(f"   ❌ Core Memory error: {e}")
    exit(1)

try:
    print("4. Testing utils...")
    from utils.data_loader import DataLoader
    print("   ✅ Utils imported successfully")
except Exception as e:
    print(f"   ❌ Utils error: {e}")
    exit(1)

try:
    print("5. Testing analyzers...")
    from analyzers.statistical_analyzer import StatisticalAnalyzer
    from analyzers.pattern_detector import PatternDetector
    from analyzers.insight_generator import InsightGenerator
    print("   ✅ Analyzers imported successfully")
except Exception as e:
    print(f"   ❌ Analyzers error: {e}")
    exit(1)

try:
    print("6. Testing chatbot...")
    from chatbot.qa_chain import DataContextManager
    print("   ✅ Chatbot imported successfully")
except Exception as e:
    print(f"   ❌ Chatbot error: {e}")
    exit(1)

print("-" * 50)
print("🎉 All imports successful!")
print("\nYou can now run: streamlit run app.py")
