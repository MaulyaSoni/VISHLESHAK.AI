"""
Continuous Improvement Loop for FINBOT v4
Orchestrates the feedback → learning → improvement cycle
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from chatbot.quality_scorer import get_quality_scorer, QualityScore
from chatbot.feedback_collector import get_feedback_collector, FeedbackType
from chatbot.preference_learner import get_preference_learner
from chatbot.response_formatter import get_response_formatter

logger = logging.getLogger(__name__)


class ImprovementLoop:
    """
    Continuous improvement orchestrator
    
    Cycle:
    1. Generate response
    2. Evaluate quality
    3. Collect feedback
    4. Learn preferences
    5. Adapt future responses
    
    Features:
    - Automated quality evaluation
    - Feedback-driven learning
    - Progressive improvement
    - Performance tracking
    
    Usage:
        loop = ImprovementLoop()
        result = loop.process_response(question, response, context)
    """
    
    def __init__(self):
        """Initialize improvement loop"""
        self.quality_scorer = get_quality_scorer()
        self.feedback_collector = get_feedback_collector()
        self.preference_learner = get_preference_learner()
        self.response_formatter = get_response_formatter()
        
        # Performance tracking
        self.cycle_count = 0
        self.avg_quality_over_time = []
        
        logger.info("✅ Improvement loop initialized")
    
    def process_response(
        self,
        question: str,
        response: str,
        user_id: str,
        session_id: str,
        message_id: int,
        data_context: Optional[str] = None,
        chat_context: str = None,
        question_type: str = "analytical"  # Optional: analytical, factual, conversational
    ) -> Dict[str, Any]:
        """
        Process response through improvement loop
        
        Args:
            question: User's question
            response: Generated response
            user_id: User identifier
            session_id: Session identifier
            message_id: Message ID
            data_context: Data context
            chat_context: Chat context
            
        Returns:
            Dict with formatted response and quality info
        """
        logger.info(f"🔄 Processing through improvement loop (cycle {self.cycle_count + 1})")
        
        # Step 1: Evaluate quality
        quality_score = self.quality_scorer.evaluate(
            question=question,
            response=response,
            context=chat_context,
            data_context=data_context
        )
        
        logger.info(f"Quality score: {quality_score.overall_score:.1f}/100 (Grade: {quality_score.get_grade()})")
        
        # Step 2: Format response
        formatted_response = self.response_formatter.format_response(
            response=response,
            response_type="standard",
            quality_score=quality_score.overall_score
        )
        
        # Step 3: Track metrics
        self.cycle_count += 1
        self.avg_quality_over_time.append(quality_score.overall_score)
        
        # Step 4: Prepare for feedback collection
        response_metadata = {
            "response_length": len(response),
            "had_visualization": "chart" in response.lower() or "plot" in response.lower(),
            "showed_reasoning": "reasoning" in response.lower() or "step" in response.lower(),
            "technical_level": self._detect_technical_level(response),
            "used_tables": "|" in response or "table" in response.lower(),
            "quality_score": quality_score.overall_score,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "formatted_response": formatted_response,
            "quality_score": quality_score,
            "response_metadata": response_metadata,
            "cycle_number": self.cycle_count,
            "improvement_suggestions": quality_score.suggestions
        }
    
    def handle_feedback(
        self,
        user_id: str,
        session_id: str,
        message_id: int,
        feedback_type: FeedbackType,
        feedback_value: int,
        question_text: str,
        response_text: str,
        response_metadata: Dict[str, Any],
        comment: Optional[str] = None  # Optional user comment
    ):
        """
        Handle user feedback and trigger learning
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            message_id: Message ID
            feedback_type: Type of feedback
            feedback_value: Feedback value
            question_text: Original question
            response_text: Response that was given
            response_metadata: Metadata about response
        """
        logger.info(f"📥 Handling feedback: {feedback_type.value} = {feedback_value}")
        
        # Step 1: Collect feedback
        self.feedback_collector.add_feedback(
            session_id=session_id,
            user_id=user_id,
            message_id=message_id,
            feedback_type=feedback_type,
            feedback_value=feedback_value,
            feedback_text=comment,  # Use the comment parameter
            question_text=question_text,
            response_text=response_text
        )
        
        # Step 2: Learn from feedback
        self.preference_learner.learn_from_feedback(
            user_id=user_id,
            feedback_type=feedback_type,
            feedback_value=feedback_value,
            response_metadata=response_metadata
        )
        
        logger.info("✅ Feedback processed and learned")
    
    def get_adapted_prompt(
        self,
        base_prompt: str,
        user_id: str
    ) -> str:
        """
        Get prompt adapted to user preferences
        
        Args:
            base_prompt: Base prompt
            user_id: User identifier
            
        Returns:
            Adapted prompt
        """
        return self.preference_learner.adapt_prompt_to_preferences(
            base_prompt=base_prompt,
            user_id=user_id
        )
    
    def get_improvement_metrics(self) -> Dict[str, Any]:
        """Get improvement metrics and trends"""
        if not self.avg_quality_over_time:
            return {
                "cycles": 0,
                "message": "No data yet"
            }
        
        # Calculate trends
        recent_quality = self.avg_quality_over_time[-10:] if len(self.avg_quality_over_time) >= 10 else self.avg_quality_over_time
        
        if len(recent_quality) >= 2:
            trend = recent_quality[-1] - recent_quality[0]
            trend_direction = "improving" if trend > 0 else "declining" if trend < 0 else "stable"
        else:
            trend = 0
            trend_direction = "insufficient_data"
        
        # Get quality scorer trends
        quality_trends = self.quality_scorer.get_trend_analysis(last_n=10)
        
        # Get recommendations
        recommendations = self.quality_scorer.get_improvement_recommendations()
        
        return {
            "total_cycles": self.cycle_count,
            "avg_quality_recent": sum(recent_quality) / len(recent_quality),
            "avg_quality_all_time": sum(self.avg_quality_over_time) / len(self.avg_quality_over_time),
            "trend": trend,
            "trend_direction": trend_direction,
            "quality_trends": quality_trends,
            "recommendations": recommendations
        }
    
    def _detect_technical_level(self, response: str) -> str:
        """Detect technical level of response"""
        technical_terms = [
            "correlation", "regression", "statistical", "hypothesis",
            "variance", "deviation", "coefficient", "algorithm"
        ]
        
        response_lower = response.lower()
        technical_count = sum(1 for term in technical_terms if term in response_lower)
        
        if technical_count >= 3:
            return "technical"
        elif technical_count >= 1:
            return "moderate"
        else:
            return "simple"


# Global instance
_improvement_loop = None

def get_improvement_loop() -> ImprovementLoop:
    """Get global improvement loop instance"""
    global _improvement_loop
    if _improvement_loop is None:
        _improvement_loop = ImprovementLoop()
    return _improvement_loop
