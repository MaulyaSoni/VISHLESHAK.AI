"""
Agent Memory - Stores tool usage history and learns from success/failure
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class AgentMemory:
    """
    Stores and learns from tool usage patterns
    """
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.tool_history: List[Dict] = []
        self.tool_stats = defaultdict(lambda: {
            "total_uses": 0,
            "successes": 0,
            "failures": 0,
            "avg_time": 0.0,
            "success_rate": 0.0,
        })
        self.context_tool_map = defaultdict(list)  # question type → tools used
    
    def record_tool_use(
        self,
        tool_name: str,
        success: bool,
        execution_time: float,
        context: Optional[Dict] = None,
    ):
        """Record tool usage"""
        entry = {
            "tool": tool_name,
            "success": success,
            "time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
        }
        
        self.tool_history.append(entry)
        
        # Maintain max history
        if len(self.tool_history) > self.max_history:
            self.tool_history = self.tool_history[-self.max_history:]
        
        # Update stats
        stats = self.tool_stats[tool_name]
        stats["total_uses"] += 1
        
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
        
        stats["success_rate"] = stats["successes"] / stats["total_uses"]
        
        # Update avg time (exponential moving average)
        alpha = 0.3
        stats["avg_time"] = alpha * execution_time + (1 - alpha) * stats["avg_time"]
        
        # Update context mapping
        if context and "question_type" in context:
            qtype = context["question_type"]
            if tool_name not in self.context_tool_map[qtype]:
                self.context_tool_map[qtype].append(tool_name)
    
    def get_tool_stats(self, tool_name: str) -> Dict:
        """Get statistics for a tool"""
        return dict(self.tool_stats.get(tool_name, {}))
    
    def get_recommended_tools(self, question_type: str, top_k: int = 3) -> List[str]:
        """Get recommended tools for a question type"""
        tools = self.context_tool_map.get(question_type, [])
        
        if not tools:
            # No history, return top performing tools overall
            sorted_tools = sorted(
                self.tool_stats.items(),
                key=lambda x: (x[1]["success_rate"], x[1]["total_uses"]),
                reverse=True,
            )
            return [t[0] for t in sorted_tools[:top_k]]
        
        # Sort by success rate
        tool_scores = [
            (t, self.tool_stats[t]["success_rate"])
            for t in tools
            if t in self.tool_stats
        ]
        tool_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [t[0] for t in tool_scores[:top_k]]
    
    def get_all_stats(self) -> Dict:
        """Get all statistics"""
        return {
            "total_entries": len(self.tool_history),
            "tool_stats": dict(self.tool_stats),
            "context_map": dict(self.context_tool_map),
        }
    
    def clear_old_entries(self, days: int = 30):
        """Clear entries older than N days"""
        cutoff = datetime.now() - timedelta(days=days)
        self.tool_history = [
            e for e in self.tool_history
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]
        
        logger.info(f"Cleared old entries, {len(self.tool_history)} remain")


# Global instance
_agent_memory = None

def get_agent_memory() -> AgentMemory:
    """Get global agent memory instance"""
    global _agent_memory
    if _agent_memory is None:
        _agent_memory = AgentMemory()
    return _agent_memory
