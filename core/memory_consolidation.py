"""
Memory Consolidation System
Like "sleep consolidation" in human brain - processes and summarizes memories
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from core.llm import get_chat_llm
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import memory_config

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """
    Consolidates memories through summarization and organization
    
    Inspired by memory consolidation during sleep:
    - Summarizes conversation windows
    - Extracts semantic knowledge
    - Identifies important episodes
    - Cleans up low-importance memories
    
    Usage:
        consolidator = MemoryConsolidator()
        summary = consolidator.create_summary(messages)
    """
    
    def __init__(self):
        """Initialize memory consolidator"""
        self.llm = get_chat_llm()
        self.summary_prompt = self._create_summary_prompt()
        self.extraction_prompt = self._create_extraction_prompt()
        logger.info("✅ Memory consolidator initialized")
    
    def _create_summary_prompt(self) -> PromptTemplate:
        """Create prompt for conversation summarization"""
        return PromptTemplate(
            input_variables=["conversation", "existing_summary"],
            template="""You are a memory consolidation system. Create a concise summary of this conversation.

EXISTING SUMMARY (if any):
{existing_summary}

NEW CONVERSATION:
{conversation}

Create a comprehensive but concise summary that:
1. Captures key topics discussed
2. Notes important decisions or insights
3. Identifies user preferences mentioned
4. Highlights any problems solved
5. Maintains continuity with existing summary

IMPORTANT: Keep summary under 500 words. Focus on what's important for future context.

SUMMARY:"""
        )
    
    def _create_extraction_prompt(self) -> PromptTemplate:
        """Create prompt for semantic knowledge extraction"""
        return PromptTemplate(
            input_variables=["conversation"],
            template="""Extract structured knowledge from this conversation.

CONVERSATION:
{conversation}

Extract and format as JSON:
{{
    "user_preferences": [
        {{"preference": "...", "confidence": 0.8}}
    ],
    "facts_learned": [
        {{"fact": "...", "confidence": 0.9}}
    ],
    "insights": [
        {{"insight": "...", "importance": 0.7}}
    ],
    "topics": ["topic1", "topic2"]
}}

Only extract information that is explicitly stated or strongly implied.
Use confidence scores (0-1) to indicate certainty.

EXTRACTED KNOWLEDGE:"""
        )
    
    def create_summary(
        self,
        messages: List[Dict[str, str]],
        existing_summary: Optional[str] = None
    ) -> str:
        """
        Create or update conversation summary
        
        Args:
            messages: List of message dicts with 'type' and 'content'
            existing_summary: Previous summary to build upon
            
        Returns:
            Updated summary text
        """
        if not messages:
            return existing_summary or ""
        
        # Format conversation
        conversation_text = self._format_conversation(messages)
        
        # Check token count
        token_count = len(conversation_text.split())
        if token_count > 2000:
            logger.warning(f"Conversation too long ({token_count} tokens), truncating")
            conversation_text = self._truncate_conversation(conversation_text, 2000)
        
        try:
            # Generate summary
            chain = self.summary_prompt | self.llm | StrOutputParser()
            
            summary = chain.invoke({
                "conversation": conversation_text,
                "existing_summary": existing_summary or "None"
            })
            
            logger.info(f"Created summary: {len(summary)} chars from {len(messages)} messages")
            return summary.strip()
        
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return existing_summary or ""
    
    def extract_semantic_knowledge(
        self,
        messages: List[Dict[str, str]]
    ) -> Dict[str, List]:
        """
        Extract structured knowledge from conversation
        
        Args:
            messages: List of message dicts
            
        Returns:
            Dict with extracted knowledge categories
        """
        if not messages:
            return {
                "user_preferences": [],
                "facts_learned": [],
                "insights": [],
                "topics": []
            }
        
        conversation_text = self._format_conversation(messages)
        
        try:
            # Extract knowledge
            chain = self.extraction_prompt | self.llm | StrOutputParser()
            
            result = chain.invoke({
                "conversation": conversation_text
            })
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            knowledge = json.loads(json_str)
            
            logger.info(f"Extracted {len(knowledge.get('facts_learned', []))} facts, "
                       f"{len(knowledge.get('user_preferences', []))} preferences")
            
            return knowledge
        
        except Exception as e:
            logger.error(f"Error extracting knowledge: {e}")
            return {
                "user_preferences": [],
                "facts_learned": [],
                "insights": [],
                "topics": []
            }
    
    def identify_episodes(
        self,
        messages: List[Dict[str, str]],
        importance_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Identify important episodic memories
        
        Args:
            messages: List of message dicts with importance scores
            importance_threshold: Minimum importance to be an episode
            
        Returns:
            List of episode dicts
        """
        episodes = []
        
        # Look for sequences of high-importance messages
        current_episode = []
        episode_start_idx = 0
        
        for i, msg in enumerate(messages):
            importance = msg.get('importance_score', 0.5)
            
            if importance >= importance_threshold:
                if not current_episode:
                    episode_start_idx = i
                current_episode.append(msg)
            else:
                # End of episode sequence
                if len(current_episode) >= 2:  # At least 2 messages
                    episodes.append({
                        "messages": current_episode,
                        "start_index": episode_start_idx,
                        "end_index": i - 1,
                        "avg_importance": sum(m.get('importance_score', 0.5) 
                                            for m in current_episode) / len(current_episode)
                    })
                current_episode = []
        
        # Handle last episode
        if len(current_episode) >= 2:
            episodes.append({
                "messages": current_episode,
                "start_index": episode_start_idx,
                "end_index": len(messages) - 1,
                "avg_importance": sum(m.get('importance_score', 0.5) 
                                    for m in current_episode) / len(current_episode)
            })
        
        logger.info(f"Identified {len(episodes)} episodic memories")
        return episodes
    
    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into readable conversation"""
        lines = []
        for msg in messages:
            role = "User" if msg['type'] == 'human' else "Assistant"
            content = msg['content']
            lines.append(f"{role}: {content}")
        
        return "\n\n".join(lines)
    
    def _truncate_conversation(self, text: str, max_words: int) -> str:
        """Truncate conversation to max words"""
        words = text.split()
        if len(words) <= max_words:
            return text
        
        # Keep beginning and end
        keep_words = max_words // 2
        truncated = (
            " ".join(words[:keep_words]) + 
            "\n\n[... conversation truncated ...]\n\n" +
            " ".join(words[-keep_words:])
        )
        
        return truncated
    
    def calculate_compression_ratio(
        self,
        original_text: str,
        summary: str
    ) -> float:
        """Calculate compression ratio"""
        original_len = len(original_text.split())
        summary_len = len(summary.split())
        
        if original_len == 0:
            return 0.0
        
        return summary_len / original_len


# Global instance
_memory_consolidator = None

def get_memory_consolidator() -> MemoryConsolidator:
    """Get global memory consolidator instance"""
    global _memory_consolidator
    if _memory_consolidator is None:
        _memory_consolidator = MemoryConsolidator()
    return _memory_consolidator
