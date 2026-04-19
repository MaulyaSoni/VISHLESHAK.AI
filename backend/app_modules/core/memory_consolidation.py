"""
Memory Consolidation System
Like "sleep consolidation" in human brain - processes and summarizes memories
Also handles 3-tier dataset memory summarization (Hot/Warm/Cold)
"""

import os
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

from core.llm import get_chat_llm
from langchain_core.prompts import PromptTemplate
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

    def _compute_dataset_hash(self, df: pd.DataFrame) -> str:
        """Compute hash for dataset based on columns and shape"""
        col_hash = "_".join(sorted(df.columns))
        shape_str = f"{df.shape[0]}_{df.shape[1]}"
        return hashlib.md5(f"{col_hash}_{shape_str}".encode()).hexdigest()[:12]

    def summarize_dataset(self, df: pd.DataFrame, domain: str = "general") -> Dict[str, Any]:
        """
        Create dataset summary using Groq LLM (llama-3.3-70b-versatile)
        
        Used for Tier 2 (Warm) memory - per-dataset summaries
        
        Args:
            df: DataFrame to summarize
            domain: Domain context (finance/insurance/ecommerce/general)
        
        Returns:
            Dict with key_findings, anomalies, column_stats, date_analysed
        """
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()[:5]
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()[:3]
        
        stats_summary = []
        for col in numeric_cols:
            stats_summary.append({
                "column": col,
                "mean": round(float(df[col].mean()), 2),
                "std": round(float(df[col].std()), 2),
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2),
                "nulls": int(df[col].isnull().sum())
            })
        
        prompt = f"""Summarise this dataset analysis in 5 bullet points.
Highlight anomalies, trends, and key stats. Max 300 words.

Dataset Info:
- Rows: {len(df)}, Columns: {len(df.columns)}
- Numeric: {numeric_cols}
- Categorical: {cat_cols}
- Stats: {json.dumps(stats_summary)[:500]}
- Domain: {domain}

SUMMARY:"""

        try:
            llm = get_chat_llm()
            chain = llm | StrOutputParser()
            summary = chain.invoke(prompt).strip()
            
            return {
                "key_findings": summary[:500],
                "anomalies": self._detect_data_anomalies(df),
                "column_stats": stats_summary,
                "date_analysed": datetime.now().isoformat(),
                "domain": domain,
                "dataset_hash": self._compute_dataset_hash(df)
            }
        
        except Exception as e:
            logger.error(f"Dataset summarization failed: {e}")
            return {
                "key_findings": "Analysis completed",
                "anomalies": [],
                "column_stats": stats_summary,
                "date_analysed": datetime.now().isoformat(),
                "domain": domain
            }

    def _detect_data_anomalies(self, df: pd.DataFrame) -> List[str]:
        """Detect anomalies in dataset"""
        anomalies = []
        
        for col in df.select_dtypes(include=['number']).columns[:5]:
            null_pct = df[col].isnull().sum() / len(df) * 100
            if null_pct > 15:
                anomalies.append(f"{col}: {null_pct:.1f}% missing values")
            
            q1, q3 = df[col].quantile([0.25, 0.75])
            iqr = q3 - q1
            outliers = ((df[col] < q1 - 3*iqr) | (df[col] > q3 + 3*iqr)).sum()
            if outliers > 0:
                anomalies.append(f"{col}: {outliers} extreme outliers detected")
        
        return anomalies[:5]

    def save_dataset_memory(
        self,
        user_id: str,
        summary: Dict[str, Any],
        memory_tier: str = "warm"
    ) -> str:
        """
        Save dataset memory to storage
        
        Args:
            user_id: User identifier
            summary: Dataset summary dict
            memory_tier: "warm" (Tier 2) or "cold" (Tier 3)
        
        Returns:
            Path to saved file
        """
        memory_dir = os.path.join("data", "memory", user_id)
        if memory_tier == "cold":
            memory_dir = os.path.join("storage", "memory_db", user_id)
        
        os.makedirs(memory_dir, exist_ok=True)
        
        dataset_hash = summary.get("dataset_hash", "unknown")
        file_path = os.path.join(memory_dir, f"{dataset_hash}.json")
        
        with open(file_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"✅ Saved {memory_tier} memory: {file_path}")
        return file_path

    def load_dataset_memory(
        self,
        user_id: str,
        dataset_hash: str,
        memory_tier: str = "warm"
    ) -> Optional[Dict[str, Any]]:
        """Load dataset memory from storage"""
        memory_dir = os.path.join("data", "memory", user_id)
        if memory_tier == "cold":
            memory_dir = os.path.join("storage", "memory_db", user_id)
        
        file_path = os.path.join(memory_dir, f"{dataset_hash}.json")
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        
        return None

    def find_similar_datasets(self, user_id: str, current_hash: str) -> List[Dict[str, Any]]:
        """Find similar datasets from past sessions"""
        similar = []
        
        memory_dir = os.path.join("data", "memory", user_id)
        if not os.path.exists(memory_dir):
            return similar
        
        for f in os.listdir(memory_dir):
            if not f.endswith(".json") or f == f"{current_hash}.json":
                continue
            
            try:
                with open(os.path.join(memory_dir, f), "r") as fp:
                    mem = json.load(fp)
                    similar.append({
                        "dataset_hash": f.replace(".json", ""),
                        "key_findings": mem.get("key_findings", "")[:200],
                        "date_analysed": mem.get("date_analysed", "")
                    })
            except:
                continue
        
        return similar[:3]

    def create_cross_session_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Create cross-session summary (Tier 3 - Cold memory)
        
        Weekly consolidation of all Tier 2 summaries
        """
        memory_dir = os.path.join("data", "memory", user_id)
        
        if not os.path.exists(memory_dir):
            return {}
        
        summaries = []
        for f in os.listdir(memory_dir):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(memory_dir, f), "r") as fp:
                        summaries.append(json.load(fp))
                except:
                    continue
        
        if not summaries:
            return {}
        
        prompt = f"""Create a weekly summary of all dataset analyses.
Combine key findings from {len(summaries)} analyses.
Focus on patterns across datasets and recurring insights.

SUMMARIES:
{json.dumps([s.get('key_findings', '')[:300] for s in summaries])[:1000]}

WEEKLY SUMMARY:"""

        try:
            llm = get_chat_llm()
            chain = llm | StrOutputParser()
            weekly_summary = chain.invoke(prompt).strip()
            
            cross_session = {
                "summaries": summaries,
                "weekly_summary": weekly_summary,
                "created_at": datetime.now().isoformat(),
                "datasets_analyzed": len(summaries)
            }
            
            cold_dir = os.path.join("storage", "memory_db", user_id)
            os.makedirs(cold_dir, exist_ok=True)
            
            with open(os.path.join(cold_dir, "longterm.json"), "w") as f:
                json.dump(cross_session, f, indent=2)
            
            logger.info(f"✅ Created cross-session summary: {len(summaries)} datasets")
            return cross_session
        
        except Exception as e:
            logger.error(f"Cross-session summary failed: {e}")
            return {}


# Global instance
_memory_consolidator = None

def get_memory_consolidator() -> MemoryConsolidator:
    """Get global memory consolidator instance"""
    global _memory_consolidator
    if _memory_consolidator is None:
        _memory_consolidator = MemoryConsolidator()
    return _memory_consolidator
