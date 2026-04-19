"""
Feedback Collection System for Vishleshak AI v1
Collects explicit and implicit feedback for continuous improvement
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging

from core.memory_database import get_memory_database

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback"""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    RATING = "rating"  # 1-5 stars
    COMMENT = "comment"
    IMPLICIT_POSITIVE = "implicit_positive"  # User followed suggestion
    IMPLICIT_NEGATIVE = "implicit_negative"  # User ignored or asked again


class FeedbackCollector:
    """
    Collect and manage user feedback
    
    Features:
    - Multiple feedback types
    - Explicit and implicit feedback
    - Detailed feedback storage
    - Analytics and insights
    
    Usage:
        collector = FeedbackCollector()
        collector.add_feedback(message_id, "thumbs_up", score=1)
    """
    
    def __init__(self):
        """Initialize feedback collector"""
        self.database = get_memory_database()
        
        # Feedback statistics
        self.stats = {
            "total_feedback": 0,
            "by_type": {},
            "positive_ratio": 0.0
        }
        
        logger.info("✅ Feedback collector initialized")
    
    def add_feedback(
        self,
        session_id: str,
        user_id: str,
        message_id: int,
        feedback_type: FeedbackType,
        feedback_value: Optional[int] = None,
        feedback_text: Optional[str] = None,
        question_text: Optional[str] = None,
        response_text: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add feedback for a response
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            message_id: Message being rated
            feedback_type: Type of feedback
            feedback_value: Numeric value (1-5 for rating, 1/-1 for thumbs)
            feedback_text: Optional text comment
            question_text: The question that was asked
            response_text: The response that was given
            metadata: Additional metadata
            
        Returns:
            Feedback ID
        """
        # Normalize feedback value
        if feedback_type == FeedbackType.THUMBS_UP:
            feedback_value = 1
        elif feedback_type == FeedbackType.THUMBS_DOWN:
            feedback_value = -1
        elif feedback_type == FeedbackType.IMPLICIT_POSITIVE:
            feedback_value = 1
        elif feedback_type == FeedbackType.IMPLICIT_NEGATIVE:
            feedback_value = -1
        
        # Save to database
        self.database.save_feedback(
            session_id=session_id,
            user_id=user_id,
            message_id=message_id,
            feedback_type=feedback_type.value,
            feedback_value=feedback_value,
            feedback_text=feedback_text,
            question_text=question_text,
            response_text=response_text
        )
        
        # Update statistics
        self.stats["total_feedback"] += 1
        self.stats["by_type"][feedback_type.value] = \
            self.stats["by_type"].get(feedback_type.value, 0) + 1
        
        logger.info(f"Feedback collected: {feedback_type.value} for message {message_id}")
        
        return message_id
    
    def detect_implicit_feedback(
        self,
        current_question: str,
        previous_question: Optional[str],
        previous_response: Optional[str],
        user_action: str  # "followed_suggestion", "repeated_question", "refined_question"
    ) -> Optional[FeedbackType]:
        """
        Detect implicit feedback from user behavior
        
        Args:
            current_question: Current question
            previous_question: Previous question
            previous_response: Previous response
            user_action: Action taken
            
        Returns:
            Detected feedback type or None
        """
        if user_action == "followed_suggestion":
            # User followed a suggestion from the response - positive signal
            return FeedbackType.IMPLICIT_POSITIVE
        
        elif user_action == "repeated_question":
            # User asked the same question again - negative signal
            if previous_question and self._are_similar_questions(current_question, previous_question):
                return FeedbackType.IMPLICIT_NEGATIVE
        
        elif user_action == "refined_question":
            # User refined their question - neutral to slightly negative
            if previous_question and self._is_refinement(current_question, previous_question):
                return FeedbackType.IMPLICIT_NEGATIVE
        
        return None
    
    def _are_similar_questions(self, q1: str, q2: str) -> bool:
        """Check if questions are similar"""
        # Simple similarity check
        q1_words = set(q1.lower().split())
        q2_words = set(q2.lower().split())
        
        if not q1_words or not q2_words:
            return False
        
        overlap = len(q1_words & q2_words)
        similarity = overlap / max(len(q1_words), len(q2_words))
        
        return similarity > 0.6
    
    def _is_refinement(self, current: str, previous: str) -> bool:
        """Check if current is a refinement of previous"""
        # Simple heuristic: shares some words but has "more specific" indicators
        refinement_indicators = [
            "specifically", "exactly", "particularly", "what about",
            "how about", "can you", "more details"
        ]
        
        current_lower = current.lower()
        
        # Check for refinement indicators
        has_indicators = any(ind in current_lower for ind in refinement_indicators)
        
        # Check for shared concepts
        shares_concepts = self._are_similar_questions(current, previous)
        
        return has_indicators and shares_concepts
    
    def get_feedback_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get feedback summary for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Summary dict with statistics
        """
        stats = self.database.get_feedback_stats(user_id)
        
        if not stats or stats.get('total_feedback', 0) == 0:
            return {
                "total_feedback": 0,
                "positive_ratio": 0.0,
                "message": "No feedback collected yet"
            }
        
        positive = stats.get('positive', 0)
        total = stats.get('total_feedback', 0)
        
        return {
            "total_feedback": total,
            "positive": positive,
            "negative": stats.get('negative', 0),
            "positive_ratio": positive / total if total > 0 else 0.0,
            "avg_rating": stats.get('avg_rating', 0.0)
        }
    
    def get_low_rated_responses(
        self,
        user_id: str,
        min_rating: float = 2.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get responses with low ratings for analysis
        
        Args:
            user_id: User identifier
            min_rating: Minimum rating threshold
            limit: Max results
            
        Returns:
            List of low-rated responses
        """
        # This would query database for low ratings
        # Implementation depends on database schema
        return []


# Global instance
_feedback_collector = None

def get_feedback_collector() -> FeedbackCollector:
    """Get global feedback collector instance"""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector
