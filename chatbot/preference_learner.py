"""
Preference Learning Engine for FINBOT v4
Learns and adapts to user preferences through feedback
"""

from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import logging
import json

from core.memory_database import get_memory_database
from chatbot.feedback_collector import FeedbackType

logger = logging.getLogger(__name__)


class PreferenceLearner:
    """
    Learn user preferences from feedback and behavior
    
    Learning Categories:
    - Response style (detailed vs concise, formal vs casual)
    - Analysis depth (quick overview vs deep dive)
    - Visualization preferences (charts types, colors)
    - Communication preferences (technical vs simple)
    - Tool usage preferences (when to use which tools)
    
    Learning Methods:
    - Explicit feedback (ratings, comments)
    - Implicit feedback (behavior patterns)
    - Reinforcement learning approach (reward good, penalize bad)
    
    Usage:
        learner = PreferenceLearner()
        learner.update_preferences(user_id, feedback)
        preferences = learner.get_user_preferences(user_id)
    """
    
    def __init__(self):
        """Initialize preference learner"""
        self.database = get_memory_database()
        
        # Preference categories
        self.preference_categories = {
            "response_style": ["detailed", "concise", "balanced"],
            "response_tone": ["formal", "casual", "professional"],
            "analysis_depth": ["quick", "moderate", "comprehensive"],
            "technical_level": ["simple", "moderate", "technical"],
            "visualization": ["always", "when_helpful", "rarely"],
            "reasoning_visibility": ["show_steps", "hide_steps", "summary_only"],
            "data_presentation": ["tables", "bullets", "prose"],
        }
        
        # Learning rates
        self.learning_rate = 0.1  # How quickly to adapt
        self.confidence_threshold = 0.7  # Minimum confidence to apply preference
        
        logger.info("✅ Preference learner initialized")
    
    def learn_from_feedback(
        self,
        user_id: str,
        feedback_type: FeedbackType,
        feedback_value: int,
        response_metadata: Dict[str, Any]
    ):
        """
        Update preferences based on feedback
        
        Args:
            user_id: User identifier
            feedback_type: Type of feedback
            feedback_value: Numeric value (positive/negative)
            response_metadata: Metadata about the response that was rated
        """
        logger.debug(f"Learning from feedback: {feedback_type.value} = {feedback_value}")
        
        # Extract response characteristics
        response_length = response_metadata.get("response_length", 0)
        had_visualization = response_metadata.get("had_visualization", False)
        showed_reasoning = response_metadata.get("showed_reasoning", False)
        technical_level = response_metadata.get("technical_level", "moderate")
        used_tables = response_metadata.get("used_tables", False)
        
        # Determine if feedback was positive
        is_positive = feedback_value > 0
        
        # Learn response style preference
        if response_length < 200:
            style = "concise"
        elif response_length > 800:
            style = "detailed"
        else:
            style = "balanced"
        
        self._update_preference(
            user_id=user_id,
            category="response_style",
            value=style,
            is_positive=is_positive
        )
        
        # Learn visualization preference
        if had_visualization:
            self._update_preference(
                user_id=user_id,
                category="visualization",
                value="always" if is_positive else "when_helpful",
                is_positive=is_positive
            )
        
        # Learn reasoning visibility preference
        if showed_reasoning:
            self._update_preference(
                user_id=user_id,
                category="reasoning_visibility",
                value="show_steps" if is_positive else "summary_only",
                is_positive=is_positive
            )
        
        # Learn technical level preference
        self._update_preference(
            user_id=user_id,
            category="technical_level",
            value=technical_level,
            is_positive=is_positive
        )
        
        # Learn data presentation preference
        if used_tables:
            self._update_preference(
                user_id=user_id,
                category="data_presentation",
                value="tables" if is_positive else "bullets",
                is_positive=is_positive
            )
    
    def _update_preference(
        self,
        user_id: str,
        category: str,
        value: str,
        is_positive: bool
    ):
        """
        Update a specific preference
        
        Uses reinforcement learning approach:
        - Positive feedback: Increase confidence in this preference
        - Negative feedback: Decrease confidence, explore alternatives
        """
        # Get current preference
        current_prefs = self.database.get_user_preferences(
            user_id=user_id,
            category=category
        )
        
        # Find existing preference for this value
        existing = None
        for pref in current_prefs:
            if pref['preference_key'] == value:
                existing = pref
                break
        
        if existing:
            # Update existing preference
            current_confidence = existing['confidence']
            
            if is_positive:
                # Reinforce: Increase confidence
                new_confidence = min(1.0, current_confidence + self.learning_rate)
            else:
                # Penalize: Decrease confidence
                new_confidence = max(0.0, current_confidence - self.learning_rate)
            
            # Update in database
            self.database.save_user_preference(
                user_id=user_id,
                preference_category=category,
                preference_key=value,
                preference_value=value,
                learned_from="feedback",
                confidence=new_confidence
            )
        else:
            # Create new preference
            initial_confidence = 0.6 if is_positive else 0.4
            
            self.database.save_user_preference(
                user_id=user_id,
                preference_category=category,
                preference_key=value,
                preference_value=value,
                learned_from="feedback",
                confidence=initial_confidence
            )
    
    def get_user_preferences(
        self,
        user_id: str,
        min_confidence: float = None
    ) -> Dict[str, str]:
        """
        Get learned preferences for user
        
        Args:
            user_id: User identifier
            min_confidence: Minimum confidence threshold
            
        Returns:
            Dict of category -> preferred value
        """
        if min_confidence is None:
            min_confidence = self.confidence_threshold
        
        all_prefs = self.database.get_user_preferences(user_id)
        
        # Group by category and pick highest confidence
        preferences = {}
        
        by_category = defaultdict(list)
        for pref in all_prefs:
            by_category[pref['preference_category']].append(pref)
        
        for category, prefs in by_category.items():
            # Sort by confidence
            prefs.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Get top preference if above threshold
            if prefs[0]['confidence'] >= min_confidence:
                preferences[category] = prefs[0]['preference_value']
        
        return preferences
    
    def adapt_prompt_to_preferences(
        self,
        base_prompt: str,
        user_id: str
    ) -> str:
        """
        Adapt prompt based on learned preferences
        
        Args:
            base_prompt: Original prompt
            user_id: User identifier
            
        Returns:
            Adapted prompt
        """
        preferences = self.get_user_preferences(user_id)
        
        if not preferences:
            return base_prompt
        
        # Build adaptation instructions
        adaptations = []
        
        # Response style
        if "response_style" in preferences:
            style = preferences["response_style"]
            if style == "detailed":
                adaptations.append("Provide a detailed, comprehensive response with thorough explanations.")
            elif style == "concise":
                adaptations.append("Be concise and to the point. Keep response brief.")
            else:
                adaptations.append("Provide a balanced response with appropriate detail.")
        
        # Technical level
        if "technical_level" in preferences:
            level = preferences["technical_level"]
            if level == "technical":
                adaptations.append("Use technical terminology and detailed methodology.")
            elif level == "simple":
                adaptations.append("Use simple, non-technical language. Explain concepts clearly.")
            else:
                adaptations.append("Use moderately technical language with explanations.")
        
        # Visualization
        if "visualization" in preferences:
            viz = preferences["visualization"]
            if viz == "always":
                adaptations.append("Include visualizations whenever possible.")
            elif viz == "rarely":
                adaptations.append("Only suggest visualizations if absolutely necessary.")
        
        # Reasoning visibility
        if "reasoning_visibility" in preferences:
            reasoning = preferences["reasoning_visibility"]
            if reasoning == "show_steps":
                adaptations.append("Show your reasoning steps explicitly.")
            elif reasoning == "hide_steps":
                adaptations.append("Provide direct answers without showing reasoning steps.")
        
        # Data presentation
        if "data_presentation" in preferences:
            presentation = preferences["data_presentation"]
            if presentation == "tables":
                adaptations.append("Present data in table format when applicable.")
            elif presentation == "bullets":
                adaptations.append("Use bullet points for data presentation.")
            elif presentation == "prose":
                adaptations.append("Present data in narrative prose format.")
        
        # Combine adaptations with base prompt
        if adaptations:
            adaptation_text = "\n\nUSER PREFERENCES:\n" + "\n".join(f"- {a}" for a in adaptations)
            adapted_prompt = base_prompt + adaptation_text
            
            logger.debug(f"Adapted prompt with {len(adaptations)} preferences")
            return adapted_prompt
        
        return base_prompt
    
    def get_preference_confidence(
        self,
        user_id: str,
        category: str
    ) -> float:
        """
        Get confidence level for a preference category
        
        Args:
            user_id: User identifier
            category: Preference category
            
        Returns:
            Confidence level (0-1)
        """
        prefs = self.database.get_user_preferences(
            user_id=user_id,
            category=category
        )
        
        if not prefs:
            return 0.0
        
        # Return highest confidence
        return max(p['confidence'] for p in prefs)
    
    def reset_preferences(self, user_id: str):
        """Reset all preferences for user"""
        # This would delete preferences from database
        logger.info(f"Reset preferences for user: {user_id}")


# Global instance
_preference_learner = None

def get_preference_learner() -> PreferenceLearner:
    """Get global preference learner instance"""
    global _preference_learner
    if _preference_learner is None:
        _preference_learner = PreferenceLearner()
    return _preference_learner
