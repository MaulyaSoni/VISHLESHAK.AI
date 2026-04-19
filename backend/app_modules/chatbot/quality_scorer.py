"""
Response Quality Scorer for Vishleshak AI v1
Multi-dimensional evaluation of LLM responses
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import re

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.llm import get_chat_llm

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """Quality evaluation dimensions"""
    RELEVANCE = "relevance"           # Answers the question
    ACCURACY = "accuracy"             # Factually correct
    COMPLETENESS = "completeness"     # Fully addresses question
    CLARITY = "clarity"               # Easy to understand
    CONCISENESS = "conciseness"       # Not unnecessarily verbose
    ACTIONABILITY = "actionability"   # Provides actionable insights
    FORMATTING = "formatting"         # Well-formatted and structured
    PROFESSIONALISM = "professionalism"  # Professional tone


@dataclass
class QualityScore:
    """Quality score with detailed breakdown"""
    overall_score: float  # 0-100
    dimension_scores: Dict[str, float]  # Score per dimension
    strengths: List[str]  # What was good
    weaknesses: List[str]  # What needs improvement
    suggestions: List[str]  # How to improve
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_score": self.overall_score,
            "dimension_scores": self.dimension_scores,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }
    
    def get_grade(self) -> str:
        """Get letter grade"""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"


class ResponseQualityScorer:
    """
    Evaluate response quality across multiple dimensions
    
    Scoring Strategy:
    1. Multi-dimensional evaluation (8 dimensions)
    2. LLM-as-judge for nuanced assessment
    3. Weighted scoring based on question type
    4. Actionable improvement suggestions
    
    Features:
    - Comprehensive evaluation
    - Detailed feedback
    - Trend tracking
    - Automated improvement suggestions
    
    Usage:
        scorer = ResponseQualityScorer()
        quality = scorer.evaluate(question, response, context)
    """
    
    def __init__(self):
        """Initialize quality scorer"""
        self.llm = get_chat_llm()
        
        # Evaluation prompts
        self.evaluation_prompt = self._create_evaluation_prompt()
        
        # Dimension weights by question type
        self.dimension_weights = {
            "analytical": {
                QualityDimension.ACCURACY: 0.25,
                QualityDimension.COMPLETENESS: 0.20,
                QualityDimension.RELEVANCE: 0.15,
                QualityDimension.CLARITY: 0.15,
                QualityDimension.ACTIONABILITY: 0.15,
                QualityDimension.CONCISENESS: 0.05,
                QualityDimension.FORMATTING: 0.03,
                QualityDimension.PROFESSIONALISM: 0.02,
            },
            "factual": {
                QualityDimension.ACCURACY: 0.35,
                QualityDimension.RELEVANCE: 0.25,
                QualityDimension.COMPLETENESS: 0.15,
                QualityDimension.CLARITY: 0.10,
                QualityDimension.CONCISENESS: 0.10,
                QualityDimension.FORMATTING: 0.03,
                QualityDimension.PROFESSIONALISM: 0.02,
                QualityDimension.ACTIONABILITY: 0.00,
            },
            "conversational": {
                QualityDimension.CLARITY: 0.25,
                QualityDimension.RELEVANCE: 0.20,
                QualityDimension.PROFESSIONALISM: 0.15,
                QualityDimension.COMPLETENESS: 0.15,
                QualityDimension.FORMATTING: 0.10,
                QualityDimension.ACCURACY: 0.10,
                QualityDimension.ACTIONABILITY: 0.03,
                QualityDimension.CONCISENESS: 0.02,
            }
        }
        
        # Scoring history
        self.score_history: List[QualityScore] = []
        
        logger.info("✅ Response quality scorer initialized")
    
    def _create_evaluation_prompt(self) -> PromptTemplate:
        """Create comprehensive evaluation prompt"""
        return PromptTemplate(
            input_variables=["question", "response", "context", "data_context"],
            template="""You are an expert evaluator of AI assistant responses. Evaluate this response across multiple quality dimensions.

QUESTION:
{question}

RESPONSE TO EVALUATE:
{response}

CONVERSATION CONTEXT:
{context}

DATA CONTEXT:
{data_context}

Evaluate the response on these 8 dimensions (score 0-10 for each):

1. **RELEVANCE** (0-10): Does it answer the question asked?
2. **ACCURACY** (0-10): Is the information factually correct?
3. **COMPLETENESS** (0-10): Does it fully address all aspects of the question?
4. **CLARITY** (0-10): Is it easy to understand?
5. **CONCISENESS** (0-10): Is it appropriately concise without being too brief?
6. **ACTIONABILITY** (0-10): Does it provide actionable insights or next steps?
7. **FORMATTING** (0-10): Is it well-formatted and easy to read?
8. **PROFESSIONALISM** (0-10): Is the tone professional and appropriate?

Provide your evaluation in this EXACT format:

SCORES:
Relevance: [0-10]
Accuracy: [0-10]
Completeness: [0-10]
Clarity: [0-10]
Conciseness: [0-10]
Actionability: [0-10]
Formatting: [0-10]
Professionalism: [0-10]

STRENGTHS:
- [List 2-3 specific strengths]

WEAKNESSES:
- [List 2-3 specific weaknesses]

SUGGESTIONS:
- [List 2-3 specific improvement suggestions]

EVALUATION:"""
        )
    
    def evaluate(
        self,
        question: str,
        response: str,
        context: Optional[str] = None,
        data_context: Optional[str] = None,
        question_type: str = "analytical"
    ) -> QualityScore:
        """
        Evaluate response quality
        
        Args:
            question: Original question
            response: Response to evaluate
            context: Conversation context
            data_context: Data context
            question_type: Type of question (analytical, factual, conversational)
            
        Returns:
            QualityScore object with detailed evaluation
        """
        logger.info(f"🎯 Evaluating response quality...")
        
        try:
            # Get LLM evaluation
            chain = self.evaluation_prompt | self.llm | StrOutputParser()
            
            evaluation = chain.invoke({
                "question": question,
                "response": response,
                "context": context or "No prior context",
                "data_context": data_context or "No data context"
            })
            
            # Parse evaluation
            dimension_scores = self._parse_scores(evaluation)
            strengths = self._parse_list_section(evaluation, "STRENGTHS:")
            weaknesses = self._parse_list_section(evaluation, "WEAKNESSES:")
            suggestions = self._parse_list_section(evaluation, "SUGGESTIONS:")
            
            # Calculate weighted overall score
            weights = self.dimension_weights.get(question_type, self.dimension_weights["analytical"])
            overall_score = self._calculate_weighted_score(dimension_scores, weights)
            
            # Create quality score object
            quality_score = QualityScore(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                strengths=strengths,
                weaknesses=weaknesses,
                suggestions=suggestions,
                timestamp=datetime.now()
            )
            
            # Store in history
            self.score_history.append(quality_score)
            
            logger.info(f"✅ Quality score: {overall_score:.1f}/100 (Grade: {quality_score.get_grade()})")
            
            return quality_score
        
        except Exception as e:
            logger.error(f"Error evaluating quality: {e}", exc_info=True)
            
            # Return default score on error
            return QualityScore(
                overall_score=50.0,
                dimension_scores={},
                strengths=[],
                weaknesses=["Error during evaluation"],
                suggestions=["Retry evaluation"],
                timestamp=datetime.now()
            )
    
    def _parse_scores(self, evaluation: str) -> Dict[str, float]:
        """Parse dimension scores from evaluation"""
        scores = {}
        
        dimension_mapping = {
            "Relevance": QualityDimension.RELEVANCE.value,
            "Accuracy": QualityDimension.ACCURACY.value,
            "Completeness": QualityDimension.COMPLETENESS.value,
            "Clarity": QualityDimension.CLARITY.value,
            "Conciseness": QualityDimension.CONCISENESS.value,
            "Actionability": QualityDimension.ACTIONABILITY.value,
            "Formatting": QualityDimension.FORMATTING.value,
            "Professionalism": QualityDimension.PROFESSIONALISM.value,
        }
        
        for display_name, internal_name in dimension_mapping.items():
            try:
                # Look for pattern: "DimensionName: X" or "DimensionName: X/10"
                pattern = rf"{display_name}:\s*(\d+(?:\.\d+)?)"
                match = re.search(pattern, evaluation, re.IGNORECASE)
                
                if match:
                    score = float(match.group(1))
                    # Normalize to 0-10 if needed
                    if score > 10:
                        score = score / 10
                    scores[internal_name] = score
                else:
                    # Default score if not found
                    scores[internal_name] = 5.0
            
            except Exception as e:
                logger.warning(f"Could not parse score for {display_name}: {e}")
                scores[internal_name] = 5.0
        
        return scores
    
    def _parse_list_section(self, evaluation: str, section_header: str) -> List[str]:
        """Parse bulleted list section from evaluation"""
        items = []
        
        try:
            # Find section
            if section_header in evaluation:
                # Get content after header
                start_idx = evaluation.index(section_header) + len(section_header)
                
                # Find next section or end
                next_sections = ["WEAKNESSES:", "SUGGESTIONS:", "EVALUATION:", "SCORES:"]
                end_idx = len(evaluation)
                
                for next_section in next_sections:
                    if next_section in evaluation[start_idx:]:
                        potential_end = evaluation.index(next_section, start_idx)
                        if potential_end < end_idx:
                            end_idx = potential_end
                
                section_content = evaluation[start_idx:end_idx].strip()
                
                # Parse bulleted items
                lines = section_content.split('\n')
                for line in lines:
                    line = line.strip()
                    # Remove bullet points
                    if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                        item = line[1:].strip()
                        if item:
                            items.append(item)
        
        except Exception as e:
            logger.warning(f"Could not parse section {section_header}: {e}")
        
        return items
    
    def _calculate_weighted_score(
        self,
        dimension_scores: Dict[str, float],
        weights: Dict[QualityDimension, float]
    ) -> float:
        """Calculate weighted overall score"""
        total_score = 0.0
        total_weight = 0.0
        
        for dimension, weight in weights.items():
            score = dimension_scores.get(dimension.value, 5.0)
            total_score += score * weight * 10  # Convert to 0-100 scale
            total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        else:
            return 50.0
    
    def get_trend_analysis(self, last_n: int = 10) -> Dict[str, Any]:
        """
        Analyze quality trends over last N evaluations
        
        Args:
            last_n: Number of recent evaluations to analyze
            
        Returns:
            Trend analysis dict
        """
        if not self.score_history:
            return {
                "message": "No evaluation history available",
                "count": 0
            }
        
        # Get last N scores
        recent_scores = self.score_history[-last_n:]
        
        if not recent_scores:
            return {"message": "No scores in range", "count": 0}
        
        # Calculate averages
        avg_overall = sum(s.overall_score for s in recent_scores) / len(recent_scores)
        
        # Calculate dimension averages
        dimension_avgs = {}
        for dimension in QualityDimension:
            scores = [
                s.dimension_scores.get(dimension.value, 0)
                for s in recent_scores
            ]
            if scores:
                dimension_avgs[dimension.value] = sum(scores) / len(scores)
        
        # Identify trending dimensions
        if len(recent_scores) >= 3:
            # Compare first half vs second half
            mid = len(recent_scores) // 2
            first_half = recent_scores[:mid]
            second_half = recent_scores[mid:]
            
            improving = []
            declining = []
            
            for dimension in QualityDimension:
                first_avg = sum(
                    s.dimension_scores.get(dimension.value, 0) for s in first_half
                ) / len(first_half) if first_half else 0
                
                second_avg = sum(
                    s.dimension_scores.get(dimension.value, 0) for s in second_half
                ) / len(second_half) if second_half else 0
                
                diff = second_avg - first_avg
                
                if diff > 0.5:
                    improving.append(dimension.value)
                elif diff < -0.5:
                    declining.append(dimension.value)
        else:
            improving = []
            declining = []
        
        # Most common weaknesses
        all_weaknesses = []
        for score in recent_scores:
            all_weaknesses.extend(score.weaknesses)
        
        weakness_counts = {}
        for weakness in all_weaknesses:
            # Simple keyword extraction
            keywords = weakness.lower().split()
            for keyword in keywords:
                if len(keyword) > 4:  # Ignore short words
                    weakness_counts[keyword] = weakness_counts.get(keyword, 0) + 1
        
        top_weaknesses = sorted(
            weakness_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "count": len(recent_scores),
            "avg_overall_score": avg_overall,
            "avg_grade": self._score_to_grade(avg_overall),
            "dimension_averages": dimension_avgs,
            "improving_dimensions": improving,
            "declining_dimensions": declining,
            "common_weaknesses": [w[0] for w in top_weaknesses],
            "best_score": max(s.overall_score for s in recent_scores),
            "worst_score": min(s.overall_score for s in recent_scores)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def get_improvement_recommendations(self) -> List[str]:
        """Get actionable improvement recommendations based on history"""
        if len(self.score_history) < 3:
            return ["Need more evaluations to provide recommendations"]
        
        # Analyze trends
        trend = self.get_trend_analysis(last_n=10)
        
        recommendations = []
        
        # Check overall score
        if trend['avg_overall_score'] < 70:
            recommendations.append(
                "⚠️ Overall quality below target (70%). Focus on fundamental improvements."
            )
        
        # Check declining dimensions
        if trend['declining_dimensions']:
            for dim in trend['declining_dimensions']:
                recommendations.append(
                    f"📉 {dim.title()} is declining. Review recent responses for {dim} issues."
                )
        
        # Check common weaknesses
        if trend['common_weaknesses']:
            top_weakness = trend['common_weaknesses'][0]
            recommendations.append(
                f"🎯 Most common issue: '{top_weakness}'. Address in prompt engineering."
            )
        
        # Positive feedback
        if trend['improving_dimensions']:
            for dim in trend['improving_dimensions']:
                recommendations.append(
                    f"✅ {dim.title()} is improving! Continue current approach."
                )
        
        return recommendations


# Global instance
_quality_scorer = None

def get_quality_scorer() -> ResponseQualityScorer:
    """Get global quality scorer instance"""
    global _quality_scorer
    if _quality_scorer is None:
        _quality_scorer = ResponseQualityScorer()
    return _quality_scorer
