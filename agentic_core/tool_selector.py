"""
Smart Tool Selector
Chooses best tools based on question + past performance
"""

import logging
from typing import List, Dict, Any
import re

from config import agent_config
from .agent_memory import get_agent_memory

logger = logging.getLogger(__name__)


class ToolSelector:
    """
    Intelligent tool selection based on:
    - Question analysis
    - Tool descriptions
    - Historical success rates
    - Context similarity
    """
    
    def __init__(self):
        self.memory = get_agent_memory()
        self.strategy = agent_config.TOOL_SELECTION_STRATEGY
    
    def select_tools(
        self,
        question: str,
        available_tools: List[Any],
        max_tools: int = None,
    ) -> List[Any]:
        """
        Select most relevant tools for question
        """
        if max_tools is None:
            max_tools = agent_config.MAX_TOOLS_PER_QUERY
        
        question_type = self._classify_question(question)
        keywords = self._extract_keywords(question)
        
        logger.info(f"Question type: {question_type}, Keywords: {keywords[:5]}")
        
        tool_scores = []
        for tool in available_tools:
            score = self._score_tool(tool, question_type, keywords)
            tool_scores.append((tool, score))
        
        tool_scores.sort(key=lambda x: x[1], reverse=True)
        selected = [t[0] for t in tool_scores[:max_tools]]
        
        logger.info(f"Selected {len(selected)} tools: {[getattr(t,'name',str(t)) for t in selected]}")
        
        return selected
    
    def _classify_question(self, question: str) -> str:
        q_lower = question.lower()
        patterns = {
            "statistical": r"(mean|median|average|std|distribution|variance|test)",
            "correlation": r"(correlat|relationship|associat|depend|connect)",
            "anomaly": r"(outlier|anomal|unusual|strange|odd|weird)",
            "trend": r"(trend|pattern|over time|change|increase|decrease)",
            "forecast": r"(predict|forecast|future|expect|project)",
            "comparison": r"(compare|difference|between|versus|vs)",
            "visualization": r"(chart|plot|graph|visualiz|show|display)",
        }
        for qtype, pattern in patterns.items():
            if re.search(pattern, q_lower):
                return qtype
        return "general"
    
    def _extract_keywords(self, question: str) -> List[str]:
        words = question.lower().split()
        stopwords = {"the", "a", "an", "is", "are", "what", "how", "why", "can", "you"}
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        return keywords
    
    def _score_tool(self, tool: Any, question_type: str, keywords: List[str]) -> float:
        score = 0.0
        tool_name = getattr(tool, "name", "").lower()
        tool_desc = getattr(tool, "description", "").lower()
        relevance = 0.0
        for keyword in keywords:
            if keyword in tool_name or keyword in tool_desc:
                relevance += 1.0
        relevance = min(relevance / len(keywords), 1.0) if keywords else 0.0
        stats = self.memory.get_tool_stats(getattr(tool, "name", ""))
        success_rate = stats.get("success_rate", 0.5)
        type_match = 0.0
        if question_type in tool_name or question_type in tool_desc:
            type_match = 1.0
        if self.strategy == "relevance":
            score = relevance
        elif self.strategy == "success_rate":
            score = success_rate
        else:
            score = 0.4 * relevance + 0.4 * success_rate + 0.2 * type_match
        return score
