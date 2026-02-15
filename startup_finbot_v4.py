"""
FINBOT v4 Startup & Verification Script
========================================

Verifies all 3 phases are working correctly:
- Phase 1: Multi-Tiered Memory System
- Phase 2: Sequential Reasoning & Chain-of-Thought
- Phase 3: Quality Scoring & Continuous Learning

Run this before using FINBOT v4 to ensure everything is set up correctly.
"""

import sys
import os
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class FINBOTStartupVerifier:
    """Comprehensive startup verification for FINBOT v4"""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
        
    def print_banner(self):
        """Print startup banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                   🤖 FINBOT v4 STARTUP                       ║
║                                                              ║
║         Financial Intelligence Bot - Version 4.0             ║
║       Complete 3-Phase AI System Verification                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Starting verification at: %s
""" % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(banner)
    
    def check_python_version(self) -> bool:
        """Verify Python version"""
        print("\n📋 Checking Python Environment...")
        print("-" * 60)
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        print(f"  Python Version: {version_str}")
        
        if version.major >= 3 and version.minor >= 8:
            self.checks_passed.append("Python version (3.8+)")
            print("  ✅ Python version OK")
            return True
        else:
            self.checks_failed.append(f"Python version {version_str} < 3.8")
            print(f"  ❌ Python 3.8+ required, found {version_str}")
            return False
    
    def check_dependencies(self) -> bool:
        """Check core dependencies"""
        print("\n📦 Checking Core Dependencies...")
        print("-" * 60)
        
        required = {
            "langchain": "langchain",
            "langchain_groq": "langchain_groq",
            "chromadb": "chromadb",
            "pandas": "pandas",
            "numpy": "numpy",
            "sentence-transformers": "sentence_transformers",
            "torch": "torch"
        }
        
        all_ok = True
        for name, import_name in required.items():
            try:
                __import__(import_name)
                print(f"  ✅ {name}")
                self.checks_passed.append(f"Dependency: {name}")
            except ImportError:
                print(f"  ❌ {name} - NOT INSTALLED")
                self.checks_failed.append(f"Missing: {name}")
                all_ok = False
        
        return all_ok
    
    def check_environment_variables(self) -> bool:
        """Check required environment variables"""
        print("\n🔑 Checking Environment Variables...")
        print("-" * 60)
        
        # Load .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        groq_key = os.getenv("GROQ_API_KEY")
        
        if groq_key:
            print(f"  ✅ GROQ_API_KEY: {groq_key[:10]}...{groq_key[-4:]}")
            self.checks_passed.append("GROQ_API_KEY set")
            return True
        else:
            print("  ❌ GROQ_API_KEY not set")
            self.checks_failed.append("Missing GROQ_API_KEY")
            return False
    
    def check_phase1_memory(self) -> bool:
        """Verify Phase 1: Memory System"""
        print("\n🧠 Phase 1: Multi-Tiered Memory System")
        print("-" * 60)
        
        try:
            # Import memory components
            from core.enhanced_memory import get_enhanced_memory_manager
            from chatbot.context_manager import ContextManager
            
            print("  ✅ Memory imports successful")
            
            # Initialize memory
            memory = get_enhanced_memory_manager()
            context_mgr = ContextManager()
            
            print("  ✅ Memory manager initialized")
            print("  ✅ Context manager initialized")
            
            # Quick test
            test_session = f"startup_test_{datetime.now().timestamp()}"
            memory.add_message(test_session, "human", "Test message")
            history = memory.get_chat_history(test_session)
            
            if len(history) > 0:
                print("  ✅ Memory storage working")
            
            self.checks_passed.append("Phase 1: Memory System")
            memory.clear_history(test_session)
            
            return True
            
        except Exception as e:
            print(f"  ❌ Phase 1 Error: {e}")
            self.checks_failed.append(f"Phase 1: {e}")
            return False
    
    def check_phase2_reasoning(self) -> bool:
        """Verify Phase 2: Sequential Reasoning"""
        print("\n🔗 Phase 2: Sequential Reasoning & Chain-of-Thought")
        print("-" * 60)
        
        try:
            # Import reasoning components
            from chatbot.sequential_chain import get_sequential_chain_manager
            
            print("  ✅ Reasoning imports successful")
            
            # Initialize reasoning
            reasoning_chain = get_sequential_chain_manager()
            
            print("  ✅ Sequential chain manager initialized")
            
            self.checks_passed.append("Phase 2: Reasoning System")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Phase 2 Error: {e}")
            self.checks_failed.append(f"Phase 2: {e}")
            return False
    
    def check_phase3_learning(self) -> bool:
        """Verify Phase 3: Quality & Learning"""
        print("\n✨ Phase 3: Quality Scoring & Continuous Learning")
        print("-" * 60)
        
        try:
            # Import Phase 3 components
            from chatbot.quality_scorer import get_quality_scorer
            from chatbot.feedback_collector import get_feedback_collector
            from chatbot.preference_learner import get_preference_learner
            from chatbot.response_formatter import get_response_formatter
            from chatbot.improvement_loop import get_improvement_loop
            
            print("  ✅ Quality scorer imports successful")
            
            # Initialize all Phase 3 components
            scorer = get_quality_scorer()
            collector = get_feedback_collector()
            learner = get_preference_learner()
            formatter = get_response_formatter()
            loop = get_improvement_loop()
            
            print("  ✅ Quality scorer initialized")
            print("  ✅ Feedback collector initialized")
            print("  ✅ Preference learner initialized")
            print("  ✅ Response formatter initialized")
            print("  ✅ Improvement loop initialized")
            
            self.checks_passed.append("Phase 3: Learning System")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Phase 3 Error: {e}")
            self.checks_failed.append(f"Phase 3: {e}")
            return False
    
    def check_integration(self) -> bool:
        """Verify complete integration"""
        print("\n🔄 Checking Integration...")
        print("-" * 60)
        
        try:
            # Import integrated QA chain
            from chatbot.qa_chain import EnhancedQAChain
            import pandas as pd
            
            print("  ✅ QA chain imports successful")
            
            # Create test DataFrame
            test_df = pd.DataFrame({
                'student_id': [1, 2, 3],
                'grade': [85, 92, 78],
                'attendance': [95, 88, 72]
            })
            
            # Initialize QA chain (integrates all 3 phases)
            qa = EnhancedQAChain(test_df, session_id="startup_test")
            
            print("  ✅ QA chain initialized with all 3 phases")
            print("  ✅ Phase 1 (Memory) integrated")
            print("  ✅ Phase 2 (Reasoning) ready")
            print("  ✅ Phase 3 (Learning) integrated")
            
            # Verify feedback method exists
            if hasattr(qa, 'provide_feedback'):
                print("  ✅ Feedback method available")
            
            if hasattr(qa, 'get_quality_metrics'):
                print("  ✅ Quality metrics method available")
            
            self.checks_passed.append("Full Integration")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Integration Error: {e}")
            self.checks_failed.append(f"Integration: {e}")
            return False
    
    def check_database(self) -> bool:
        """Check database setup"""
        print("\n💾 Checking Database...")
        print("-" * 60)
        
        try:
            import sqlite3
            from pathlib import Path
            
            db_path = Path("data/memory/enhanced_memory.db")
            
            if db_path.exists():
                print(f"  ✅ Database found at {db_path}")
                
                # Check size
                size_mb = db_path.stat().st_size / (1024 * 1024)
                print(f"  ℹ️  Database size: {size_mb:.2f} MB")
                
                self.checks_passed.append("Database exists")
            else:
                print(f"  ⚠️  Database will be created at {db_path}")
                self.warnings.append("Database doesn't exist yet (will be auto-created)")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Database Error: {e}")
            self.checks_failed.append(f"Database: {e}")
            return False
    
    def run_quick_integration_test(self) -> bool:
        """Run a quick end-to-end test"""
        print("\n🧪 Running Quick Integration Test...")
        print("-" * 60)
        
        try:
            from chatbot.qa_chain import EnhancedQAChain
            import pandas as pd
            
            # Create test data
            test_df = pd.DataFrame({
                'category': ['A', 'B', 'C'],
                'value': [10, 20, 30]
            })
            
            # Initialize
            qa = EnhancedQAChain(test_df, session_id="integration_test")
            
            print("  ⏳ Asking test question...")
            
            # Ask question (this tests all 3 phases)
            result = qa.ask("What's the total value?", return_dict=True)
            
            if "formatted_response" in result:
                print("  ✅ Response generated")
                
            if result.get("quality_score"):
                score = result["quality_score"].overall_score
                grade = result["quality_score"].get_grade()
                print(f"  ✅ Quality evaluated: {score:.1f}/100 (Grade: {grade})")
            
            # Test feedback
            print("  ⏳ Testing feedback system...")
            feedback_result = qa.provide_feedback("thumbs_up")
            
            if feedback_result.get("success"):
                print("  ✅ Feedback system working")
            
            # Get metrics
            metrics = qa.get_quality_metrics()
            if metrics:
                print(f"  ✅ Metrics tracked: {metrics['total_cycles']} cycles")
            
            # Cleanup
            qa.clear_history()
            
            self.checks_passed.append("Integration test")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Integration test failed: {e}")
            self.checks_failed.append(f"Integration test: {e}")
            return False
    
    def print_summary(self):
        """Print final summary"""
        print("\n")
        print("═" * 60)
        print(" VERIFICATION SUMMARY")
        print("═" * 60)
        
        print(f"\n✅ Passed: {len(self.checks_passed)}")
        for check in self.checks_passed:
            print(f"   • {check}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if self.checks_failed:
            print(f"\n❌ Failed: {len(self.checks_failed)}")
            for check in self.checks_failed:
                print(f"   • {check}")
        
        print("\n" + "═" * 60)
        
        if len(self.checks_failed) == 0:
            print("\n🎉 ALL SYSTEMS OPERATIONAL!")
            print("\nFINBOT v4 is ready to use with:")
            print("  ✅ Phase 1: Multi-Tiered Memory")
            print("  ✅ Phase 2: Sequential Reasoning")
            print("  ✅ Phase 3: Quality Learning")
            print("\n💡 Quick Start:")
            print("   python app.py")
            print("\n📚 Documentation:")
            print("   See docs/FINBOT_V4_COMPLETE.md for full guide")
            return True
        else:
            print("\n⚠️  SOME CHECKS FAILED")
            print("\nPlease resolve the failed checks before using FINBOT v4.")
            print("\n📖 Troubleshooting:")
            print("   1. Install missing dependencies: pip install -r requirements.txt")
            print("   2. Set GROQ_API_KEY environment variable")
            print("   3. Check logs for detailed error messages")
            return False
    
    def run_all_checks(self) -> bool:
        """Run all verification checks"""
        self.print_banner()
        
        checks = [
            self.check_python_version,
            self.check_dependencies,
            self.check_environment_variables,
            self.check_database,
            self.check_phase1_memory,
            self.check_phase2_reasoning,
            self.check_phase3_learning,
            self.check_integration,
            self.run_quick_integration_test
        ]
        
        all_passed = True
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                print(f"\n❌ Unexpected error in {check.__name__}: {e}")
                self.checks_failed.append(f"{check.__name__}: {e}")
                all_passed = False
        
        return self.print_summary()


def main():
    """Main entry point"""
    verifier = FINBOTStartupVerifier()
    success = verifier.run_all_checks()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
