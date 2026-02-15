"""
Importance Scorer for Memory System
LSTM-like importance weighting for memories
"""

from typing import Dict, List, Optional
import re
from datetime import datetime, timedelta
import logging
from config import memory_config

logger = logging.getLogger(__name__)


class ImportanceScorer:
    """
    Calculate importance scores for memories (LSTM-like)
    
    Inspired by how LSTM networks weight information:
    - Some information is more important (input gate)
    - Importance decays over time (forget gate)
    - Important information is reinforced (output gate)
    
    Features:
    - Multi-factor importance calculation
    - Temporal decay
    - Access-based reinforcement
    - Context-aware scoring
    
    Usage:
        scorer = ImportanceScorer()
        score = scorer.calculate_importance(message, context)
    """
    
    def __init__(self):
        """Initialize importance scorer"""
        self.factors = memory_config.IMPORTANCE_FACTORS
        self.important_keywords = memory_config.IMPORTANT_KEYWORDS
        self.length_thresholds = memory_config.LENGTH_THRESHOLDS
        logger.info("✅ Importance scorer initialized")
    
    def calculate_importance(
        self,
        message: str,
        message_type: str = "human",
        context: Optional[Dict] = None,
        user_feedback: Optional[int] = None
    ) -> float:
        """
        Calculate importance score for a message
        
        Args:
            message: Message text
            message_type: 'human' or 'ai'
            context: Additional context (previous messages, etc.)
            user_feedback: Explicit feedback (1-5 or thumbs up/down)
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        
        # Base importance
        importance = 0.5
        
        # Factor 1: Message Length
        length_score = self._score_message_length(message)
        importance += length_score * self.factors["message_length"]
        
        # Factor 2: Keyword Presence
        keyword_score = self._score_keywords(message)
        importance += keyword_score * self.factors["keyword_presence"]
        
        # Factor 3: Question Depth
        depth_score = self._score_question_depth(message, message_type)
        importance += depth_score * self.factors["question_depth"]
        
        # Factor 4: User Feedback (if provided)
        if user_feedback is not None:
            feedback_score = self._score_feedback(user_feedback)
            importance += feedback_score * self.factors["user_feedback"]
        
        # Factor 5: Temporal Recency (applied during retrieval)
        # This is calculated dynamically, not stored
        
        # Normalize to 0-1 range
        importance = max(0.0, min(1.0, importance))
        
        if memory_config.LOG_IMPORTANCE_CALCULATIONS:
            logger.debug(f"Importance calculated: {importance:.3f} for message: {message[:50]}...")
        
        return importance
    
    def _score_message_length(self, message: str) -> float:
        """
        Score based on message length
        
        Logic: Longer messages often contain more information
        Returns: -0.2 to 0.3
        """
        length = len(message)
        
        if length < self.length_thresholds["short"]:
            return -0.2  # Very short = likely less important
        elif length < self.length_thresholds["medium"]:
            return 0.0   # Medium = neutral
        else:
            return 0.3   # Long = potentially important
    
    def _score_keywords(self, message: str) -> float:
        """
        Score based on important keyword presence
        
        Logic: Certain keywords indicate importance
        Returns: 0.0 to 0.5
        """
        message_lower = message.lower()
        
        # Count important keywords
        keyword_count = sum(
            1 for keyword in self.important_keywords
            if keyword in message_lower
        )
        
        if keyword_count == 0:
            return 0.0
        elif keyword_count == 1:
            return 0.3
        else:
            return 0.5  # Multiple keywords = very important
    
    def _score_question_depth(self, message: str, message_type: str) -> float:
        """
        Score based on question complexity
        
        Logic: Complex questions deserve important answers
        Returns: -0.1 to 0.4
        """
        if message_type != "human":
            return 0.0  # Only applies to user questions
        
        # Check if it's a question
        if '?' not in message:
            return -0.1  # Not a question
        
        # Count question marks (multiple = more complex)
        question_count = message.count('?')
        
        # Check for complex question indicators
        complex_indicators = [
            'why', 'how', 'explain', 'what if', 'compare',
            'analyze', 'difference between', 'relationship',
            'correlation', 'impact', 'effect'
        ]
        
        message_lower = message.lower()
        complexity = sum(
            1 for indicator in complex_indicators
            if indicator in message_lower
        )
        
        # Calculate score
        if complexity >= 2:
            return 0.4  # Very complex question
        elif complexity == 1:
            return 0.2  # Moderately complex
        elif question_count > 1:
            return 0.2  # Multiple questions
        else:
            return 0.1  # Simple question
    
    def _score_feedback(self, feedback: int) -> float:
        """
        Score based on user feedback
        
        Args:
            feedback: 1-5 rating or -1/1 for thumbs
            
        Returns: -0.3 to 0.5
        """
        if feedback in [-1, 1]:
            # Thumbs up/down
            return 0.5 if feedback == 1 else -0.3
        
        elif 1 <= feedback <= 5:
            # 5-star rating
            normalized = (feedback - 3) / 2  # -1 to 1
            return normalized * 0.4  # Scale to -0.4 to 0.4
        
        else:
            return 0.0
    
    def calculate_decay(
        self,
        original_importance: float,
        age_days: float,
        access_count: int = 0
    ) -> float:
        """
        Calculate current importance with decay (LSTM forget gate)
        
        Args:
            original_importance: Initial importance score
            age_days: Age in days
            access_count: Number of times accessed
            
        Returns:
            Current importance with decay applied
        """
        if not memory_config.ENABLE_MEMORY_DECAY:
            return original_importance
        
        # Exponential decay
        decay_factor = memory_config.DECAY_RATE ** age_days
        
        # Access-based boost (reinforcement learning)
        access_boost = min(
            access_count * memory_config.ACCESS_BOOST_FACTOR,
            memory_config.MAX_ACCESS_BOOST
        )
        
        # Calculate effective importance
        effective_importance = (
            original_importance * decay_factor + access_boost
        )
        
        return max(0.0, min(1.0, effective_importance))
    
    def should_forget(
        self,
        importance: float,
        decay_factor: float,
        age_days: float,
        is_episodic: bool = False
    ) -> bool:
        """
        Determine if memory should be forgotten (LSTM forget gate)
        
        Args:
            importance: Current importance score
            decay_factor: Current decay factor
            age_days: Age in days
            is_episodic: Is this an episodic memory (never forget)
            
        Returns:
            True if should be forgotten
        """
        if not memory_config.FORGETTING_ENABLED:
            return False
        
        # Never forget episodic memories
        if is_episodic and memory_config.FORGETTING_PRESERVE_EPISODES:
            return False
        
        # Don't forget recent memories
        if age_days < memory_config.FORGETTING_MIN_AGE_DAYS:
            return False
        
        # Calculate effective importance
        effective_importance = importance * decay_factor
        
        # Forget if below threshold
        return effective_importance < memory_config.FORGETTING_THRESHOLD
    
    def calculate_retrieval_score(
        self,
        importance: float,
        similarity: float,
        recency: float,
        access_count: int = 0
    ) -> float:
        """
        Calculate final retrieval score (for ranking)
        
        Combines multiple factors to determine which memories to retrieve
        
        Args:
            importance: Importance score
            similarity: Semantic similarity to query
            recency: Recency score (0-1, 1=very recent)
            access_count: Times accessed
            
        Returns:
            Composite retrieval score
        """
        # Weighted combination
        retrieval_score = (
            importance * 0.3 +
            similarity * 0.4 +
            recency * 0.2 +
            min(access_count * 0.02, 0.1)  # Max 0.1 from access
        )
        
        return retrieval_score
    
    def calculate_recency_score(self, age_days: float) -> float:
        """
        Calculate recency score (0-1)
        
        Args:
            age_days: Age in days
            
        Returns:
            Recency score (1=today, 0=very old)
        """
        # Exponential decay with half-life of 30 days
        half_life = 30
        recency = 0.5 ** (age_days / half_life)
        
        return recency


# Global instance
_importance_scorer = None

def get_importance_scorer() -> ImportanceScorer:
    """Get global importance scorer instance"""
    global _importance_scorer
    if _importance_scorer is None:
        _importance_scorer = ImportanceScorer()
    return _importance_scorer
