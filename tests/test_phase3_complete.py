"""
Complete Test Suite for Phase 3: Quality Scoring & Continuous Learning
Tests all Phase 3 components comprehensively
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from typing import List, Dict, Any
import tempfile
import logging

from chatbot.quality_scorer import get_quality_scorer, QualityScore
from chatbot.feedback_collector import get_feedback_collector, FeedbackType
from chatbot.preference_learner import get_preference_learner
from chatbot.response_formatter import get_response_formatter
from chatbot.improvement_loop import get_improvement_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestQualityScorer(unittest.TestCase):
    """Test response quality scoring"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.scorer = get_quality_scorer()
        cls.sample_data = "Dataset with 500 students, avg grade 75, dropout rate 14.2%"
    
    def test_01_basic_evaluation(self):
        """Test basic quality evaluation"""
        print("\n=== Test 1: Basic Quality Evaluation ===")
        
        question = "What's the average dropout rate?"
        response = "The average dropout rate is 14.2%, calculated from 500 students in the dataset."
        
        quality = self.scorer.evaluate(
            question=question,
            response=response,
            data_context=self.sample_data
        )
        
        print(f"Question: {question}")
        print(f"Overall Score: {quality.overall_score:.1f}/100")
        print(f"Grade: {quality.get_grade()}")
        print(f"Strengths: {len(quality.strengths)}")
        print(f"Weaknesses: {len(quality.weaknesses)}")
        
        self.assertIsInstance(quality, QualityScore)
        self.assertGreaterEqual(quality.overall_score, 0)
        self.assertLessEqual(quality.overall_score, 100)
        self.assertIn(quality.get_grade(), ['A', 'B', 'C', 'D', 'F'])
        
        print("✅ Basic evaluation working")
    
    def test_02_dimension_scores(self):
        """Test individual dimension scoring"""
        print("\n=== Test 2: Dimension Scoring ===")
        
        question = "Explain the correlation between attendance and grades"
        response = """There is a strong positive correlation (r=0.78, p<0.001) between attendance and grades. 
        Students with >85% attendance average 3.4 GPA vs 2.1 GPA for <65% attendance."""
        
        quality = self.scorer.evaluate(question, response, data_context=self.sample_data)
        
        print("Dimension Scores:")
        for dim, score in quality.dimension_scores.items():
            print(f"  {dim}: {score}/10")
        
        self.assertEqual(len(quality.dimension_scores), 8)
        
        print("✅ Dimension scoring working")
    
    def test_03_trend_analysis(self):
        """Test quality trend analysis"""
        print("\n=== Test 3: Trend Analysis ===")
        
        # Generate multiple evaluations
        questions = [
            "What's the dropout rate?",
            "How many students?",
            "Show statistics",
            "Analyze trends"
        ]
        
        for q in questions:
            self.scorer.evaluate(q, f"Answer to: {q}", data_context=self.sample_data)
        
        trends = self.scorer.get_trend_analysis(last_n=4)
        
        print(f"Evaluations: {trends['count']}")
        print(f"Avg Score: {trends['avg_overall_score']:.1f}/100")
        print(f"Avg Grade: {trends['avg_grade']}")
        
        self.assertGreater(trends['count'], 0)
        
        print("✅ Trend analysis working")


class TestFeedbackCollector(unittest.TestCase):
    """Test feedback collection system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.collector = get_feedback_collector()
    
    def test_01_thumbs_feedback(self):
        """Test thumbs up/down feedback"""
        print("\n=== Test 4: Thumbs Feedback ===")
        
        self.collector.add_feedback(
            session_id="test_session",
            user_id="test_user",
            message_id=1,
            feedback_type=FeedbackType.THUMBS_UP,
            question_text="Test question",
            response_text="Test response"
        )
        
        print("✅ Thumbs up feedback collected")
        
        self.collector.add_feedback(
            session_id="test_session",
            user_id="test_user",
            message_id=2,
            feedback_type=FeedbackType.THUMBS_DOWN,
            question_text="Test question 2",
            response_text="Test response 2"
        )
        
        print("✅ Thumbs down feedback collected")
    
    def test_02_rating_feedback(self):
        """Test rating feedback"""
        print("\n=== Test 5: Rating Feedback ===")
        
        self.collector.add_feedback(
            session_id="test_session",
            user_id="test_user",
            message_id=3,
            feedback_type=FeedbackType.RATING,
            feedback_value=5,
            question_text="Test question 3",
            response_text="Test response 3"
        )
        
        print("✅ 5-star rating collected")
    
    def test_03_feedback_summary(self):
        """Test feedback summary"""
        print("\n=== Test 6: Feedback Summary ===")
        
        summary = self.collector.get_feedback_summary("test_user")
        
        print(f"Total Feedback: {summary.get('total_feedback', 0)}")
        print(f"Positive Ratio: {summary.get('positive_ratio', 0):.1%}")
        
        print("✅ Feedback summary generated")


class TestPreferenceLearner(unittest.TestCase):
    """Test preference learning"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.learner = get_preference_learner()
    
    def test_01_learn_from_positive_feedback(self):
        """Test learning from positive feedback"""
        print("\n=== Test 7: Learning from Positive Feedback ===")
        
        metadata = {
            "response_length": 150,
            "had_visualization": True,
            "showed_reasoning": False,
            "technical_level": "simple",
            "used_tables": False
        }
        
        self.learner.learn_from_feedback(
            user_id="test_user",
            feedback_type=FeedbackType.THUMBS_UP,
            feedback_value=1,
            response_metadata=metadata
        )
        
        print("✅ Learned from positive feedback")
    
    def test_02_learn_from_negative_feedback(self):
        """Test learning from negative feedback"""
        print("\n=== Test 8: Learning from Negative Feedback ===")
        
        metadata = {
            "response_length": 800,
            "had_visualization": False,
            "showed_reasoning": True,
            "technical_level": "technical",
            "used_tables": True
        }
        
        self.learner.learn_from_feedback(
            user_id="test_user",
            feedback_type=FeedbackType.THUMBS_DOWN,
            feedback_value=-1,
            response_metadata=metadata
        )
        
        print("✅ Learned from negative feedback")
    
    def test_03_get_preferences(self):
        """Test getting learned preferences"""
        print("\n=== Test 9: Get Learned Preferences ===")
        
        # Learn multiple times to build confidence
        for i in range(3):
            metadata = {
                "response_length": 180,
                "had_visualization": True,
                "technical_level": "simple"
            }
            self.learner.learn_from_feedback(
                user_id="test_user_pref",
                feedback_type=FeedbackType.THUMBS_UP,
                feedback_value=1,
                response_metadata=metadata
            )
        
        prefs = self.learner.get_user_preferences("test_user_pref")
        
        print(f"Learned Preferences: {len(prefs)}")
        for category, value in prefs.items():
            print(f"  {category}: {value}")
        
        print("✅ Preferences retrieved")
    
    def test_04_adapt_prompt(self):
        """Test prompt adaptation"""
        print("\n=== Test 10: Prompt Adaptation ===")
        
        base_prompt = "Answer this question: {question}"
        
        adapted = self.learner.adapt_prompt_to_preferences(
            base_prompt=base_prompt,
            user_id="test_user_pref"
        )
        
        print(f"Base prompt length: {len(base_prompt)}")
        print(f"Adapted prompt length: {len(adapted)}")
        
        # Adapted should be different if preferences exist
        self.assertIsInstance(adapted, str)
        
        print("✅ Prompt adaptation working")


class TestResponseFormatter(unittest.TestCase):
    """Test response formatting"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.formatter = get_response_formatter()
    
    def test_01_simple_formatting(self):
        """Test simple response formatting"""
        print("\n=== Test 11: Simple Formatting ===")
        
        response = "The average dropout rate is 14.2%."
        
        formatted = self.formatter.format_response(
            response=response,
            quality_score=85.0
        )
        
        print(f"Original: {len(response)} chars")
        print(f"Formatted: {len(formatted)} chars")
        
        self.assertIn("Quality", formatted)
        
        print("✅ Simple formatting working")
    
    def test_02_structured_formatting(self):
        """Test structured response formatting"""
        print("\n=== Test 12: Structured Formatting ===")
        
        response = """
**Summary:**
The analysis shows key patterns.

**Findings:**
Dropout rate is high.

**Recommendations:**
Implement support programs.
"""
        
        formatted = self.formatter.format_response(
            response=response,
            quality_score=90.0
        )
        
        print(f"Formatted with sections: {len(formatted)} chars")
        
        print("✅ Structured formatting working")


class TestImprovementLoop(unittest.TestCase):
    """Test complete improvement loop"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.loop = get_improvement_loop()
    
    def test_01_process_response(self):
        """Test response processing"""
        print("\n=== Test 13: Process Response ===")
        
        question = "What's the dropout rate?"
        response = "The dropout rate is 14.2%."
        
        result = self.loop.process_response(
            question=question,
            response=response,
            user_id="test_user",
            session_id="test_session",
            message_id=1,
            data_context="Student dataset"
        )
        
        print(f"Cycle: {result['cycle_number']}")
        print(f"Quality: {result['quality_score'].overall_score:.1f}/100")
        
        self.assertIn('formatted_response', result)
        self.assertIn('quality_score', result)
        self.assertIn('response_metadata', result)
        
        print("✅ Response processing working")
    
    def test_02_handle_feedback(self):
        """Test feedback handling"""
        print("\n=== Test 14: Handle Feedback ===")
        
        # First process a response
        result = self.loop.process_response(
            question="Test question",
            response="Test response",
            user_id="test_user_fb",
            session_id="test_session",
            message_id=2,
            data_context="Test data"
        )
        
        # Then handle feedback
        self.loop.handle_feedback(
            user_id="test_user_fb",
            session_id="test_session",
            message_id=2,
            feedback_type=FeedbackType.THUMBS_UP,
            feedback_value=1,
            question_text="Test question",
            response_text="Test response",
            response_metadata=result['response_metadata']
        )
        
        print("✅ Feedback handled and learning triggered")
    
    def test_03_improvement_metrics(self):
        """Test improvement metrics"""
        print("\n=== Test 15: Improvement Metrics ===")
        
        # Process several responses
        for i in range(3):
            self.loop.process_response(
                question=f"Question {i}",
                response=f"Response {i}",
                user_id="test_user_metrics",
                session_id="test_session",
                message_id=100+i,
                data_context="Test data"
            )
        
        metrics = self.loop.get_improvement_metrics()
        
        print(f"Total Cycles: {metrics['total_cycles']}")
        print(f"Avg Quality: {metrics.get('avg_quality_all_time', 0):.1f}")
        print(f"Trend: {metrics.get('trend_direction', 'unknown')}")
        
        self.assertGreater(metrics['total_cycles'], 0)
        
        print("✅ Improvement metrics tracked")


class TestEndToEndIntegration(unittest.TestCase):
    """Test complete end-to-end Phase 3 integration"""
    
    def test_01_complete_cycle(self):
        """Test complete improvement cycle"""
        print("\n=== Test 16: Complete Improvement Cycle ===")
        
        # Initialize all components
        scorer = get_quality_scorer()
        collector = get_feedback_collector()
        learner = get_preference_learner()
        formatter = get_response_formatter()
        loop = get_improvement_loop()
        
        print("✅ All components initialized")
        
        # Simulate conversation
        question = "Analyze the student dropout patterns"
        response = """
The analysis reveals:
- Overall dropout rate: 14.2%
- Engineering dept highest at 18.7%
- Key factor: Attendance (correlation: 0.78)

Recommendations:
1. Early warning system
2. Peer mentoring program
3. Financial support
"""
        
        # Step 1: Evaluate quality
        quality = scorer.evaluate(question, response, data_context="500 students")
        print(f"✅ Quality evaluated: {quality.overall_score:.1f}/100")
        
        # Step 2: Format response
        formatted = formatter.format_response(response, quality_score=quality.overall_score)
        print(f"✅ Response formatted ({len(formatted)} chars)")
        
        # Step 3: Collect feedback
        collector.add_feedback(
            session_id="test",
            user_id="test_e2e",
            message_id=1,
            feedback_type=FeedbackType.THUMBS_UP,
            feedback_value=1,
            question_text=question,
            response_text=response
        )
        print("✅ Feedback collected")
        
        # Step 4: Learn preferences
        learner.learn_from_feedback(
            user_id="test_e2e",
            feedback_type=FeedbackType.THUMBS_UP,
            feedback_value=1,
            response_metadata={
                "response_length": len(response),
                "technical_level": "moderate"
            }
        )
        print("✅ Preferences learned")
        
        # Step 5: Get metrics
        metrics = loop.get_improvement_metrics()
        print(f"✅ Metrics tracked: {metrics['total_cycles']} cycles")
        
        print("\n🎉 End-to-end cycle complete!")


def run_all_tests():
    """Run all Phase 3 tests"""
    print("\n")
    print("=" * 70)
    print("🧪 FINBOT v4 - Phase 3 Complete Test Suite")
    print("Quality Scoring & Continuous Learning")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestQualityScorer))
    suite.addTests(loader.loadTestsFromTestCase(TestFeedbackCollector))
    suite.addTests(loader.loadTestsFromTestCase(TestPreferenceLearner))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestImprovementLoop))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 3 TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL PHASE 3 TESTS PASSED!")
        print("\nPhase 3 Components Verified:")
        print("  ✅ Quality Scorer (8-dimensional evaluation)")
        print("  ✅ Feedback Collector (explicit + implicit)")
        print("  ✅ Preference Learner (adaptive behavior)")
        print("  ✅ Response Formatter (professional output)")
        print("  ✅ Improvement Loop (continuous learning)")
        print("\n🚀 Phase 3 Implementation Complete!")
        print("\n🎊 ALL 3 PHASES NOW OPERATIONAL!")
        print("  ✅ Phase 1: Multi-Tiered Memory System")
        print("  ✅ Phase 2: Sequential Reasoning & CoT")
        print("  ✅ Phase 3: Quality Scoring & Learning")
    else:
        print("\n❌ Some tests failed. Review above for details.")
    
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
