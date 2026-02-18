"""
Reflection Layer - Agent self-correction and confidence scoring
"""

import logging
import re
from typing import Dict, List, Any, Optional

from core.llm import get_chat_llm
from config import agent_config
from .prompts.reflection_prompt import REFLECTION_PROMPT

logger = logging.getLogger(__name__)


class ReflectionLayer:
    """
    Self-correction layer for agent responses
    """
    
    def __init__(self):
        self.llm = get_chat_llm()
    
    def reflect(
        self,
        question: str,
        answer: str,
        context: str,
        reasoning_trace: List[Dict],
    ) -> Dict[str, Any]:
        logger.info("🔍 Reflecting on answer quality...")
        prompt = REFLECTION_PROMPT.format(
            question=question,
            answer=answer,
            context=context,
        )
        try:
            reflection_text = self.llm.invoke(prompt).content
            parsed = self._parse_reflection(reflection_text)
            logger.info(f"💭 Reflection: Confidence={parsed['confidence']:.0f}, Verdict={parsed['verdict']}")
            return parsed
        except Exception as e:
            logger.error(f"Reflection error: {e}")
            return {
                "confidence": 50,
                "issues": ["Could not complete reflection"],
                "suggestions": [],
                "verdict": "ACCEPT",
            }
    
    def _parse_reflection(self, text: str) -> Dict:
        result = {
            "confidence": 70,
            "issues": [],
            "suggestions": [],
            "verdict": "ACCEPT",
        }
        conf_match = re.search(r"Confidence:\s*(\d+)", text, re.IGNORECASE)
        if conf_match:
            result["confidence"] = int(conf_match.group(1))
        issues_match = re.search(r"Issues:\s*(.+?)(?=Suggestions:|Verdict:|$)", text, re.DOTALL | re.IGNORECASE)
        if issues_match:
            issues_text = issues_match.group(1).strip()
            result["issues"] = [
                line.strip("- ").strip()
                for line in issues_text.split("\n")
                if line.strip() and not line.strip().lower().startswith("none")
            ]
        sugg_match = re.search(r"Suggestions:\s*(.+?)(?=Verdict:|$)", text, re.DOTALL | re.IGNORECASE)
        if sugg_match:
            sugg_text = sugg_match.group(1).strip()
            result["suggestions"] = [
                line.strip("- ").strip()
                for line in sugg_text.split("\n")
                if line.strip() and not line.strip().lower().startswith("none")
            ]
        verdict_match = re.search(r"Verdict:\s*(ACCEPT|REVISE|REJECT)", text, re.IGNORECASE)
        if verdict_match:
            result["verdict"] = verdict_match.group(1).upper()
        return result
