"""
Conversation Memory System for FINBOT
Handles chat history with summarization and persistence
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from config.settings import MEMORY_DIR, MEMORY_WINDOW_SIZE, MAX_HISTORY_LENGTH


class Message:
    """Represents a single message in the conversation"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp")
        )


class ConversationMemory:
    """
    Manages conversation history with automatic summarization
    Stores both recent window and full history
    """
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.memory_file = MEMORY_DIR / f"chat_{session_id}.json"
        self.messages: List[Message] = []
        self.summary: str = ""
        self.load_history()
    
    def add_message(self, role: str, content: str):
        """Add a new message to the conversation"""
        message = Message(role, content)
        self.messages.append(message)
        
        # Auto-save after each message
        self.save_history()
    
    def get_recent_messages(self, n: int = MEMORY_WINDOW_SIZE) -> List[Dict]:
        """Get the N most recent messages"""
        recent = self.messages[-n:] if n > 0 else self.messages
        return [msg.to_dict() for msg in recent]
    
    def get_all_messages(self) -> List[Dict]:
        """Get all messages in the conversation"""
        return [msg.to_dict() for msg in self.messages]
    
    def get_context_for_llm(self) -> List[Dict]:
        """
        Get conversation context optimized for LLM
        Returns recent messages in the format expected by LangChain
        """
        recent = self.get_recent_messages()
        
        # Convert to LangChain message format
        context = []
        for msg in recent:
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return context
    
    def clear_history(self):
        """Clear all conversation history"""
        self.messages = []
        self.summary = ""
        self.save_history()
    
    def save_history(self):
        """Persist conversation to disk"""
        data = {
            "session_id": self.session_id,
            "summary": self.summary,
            "messages": [msg.to_dict() for msg in self.messages[-MAX_HISTORY_LENGTH:]],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_history(self):
        """Load conversation from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                
                self.summary = data.get("summary", "")
                self.messages = [
                    Message.from_dict(msg) for msg in data.get("messages", [])
                ]
            except Exception as e:
                print(f"Error loading history: {e}")
                self.messages = []
                self.summary = ""
    
    def get_summary(self) -> str:
        """Get conversation summary"""
        return self.summary
    
    def set_summary(self, summary: str):
        """Update conversation summary"""
        self.summary = summary
        self.save_history()
    
    def get_message_count(self) -> int:
        """Get total number of messages"""
        return len(self.messages)


class MemoryManager:
    """
    Manages multiple conversation sessions
    """
    
    def __init__(self):
        self._sessions: Dict[str, ConversationMemory] = {}
    
    def get_session(self, session_id: str = "default") -> ConversationMemory:
        """Get or create a conversation session"""
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationMemory(session_id)
        return self._sessions[session_id]
    
    def list_sessions(self) -> List[str]:
        """List all available sessions"""
        sessions = []
        for file in MEMORY_DIR.glob("chat_*.json"):
            session_id = file.stem.replace("chat_", "")
            sessions.append(session_id)
        return sessions
    
    def delete_session(self, session_id: str):
        """Delete a conversation session"""
        memory_file = MEMORY_DIR / f"chat_{session_id}.json"
        if memory_file.exists():
            memory_file.unlink()
        
        if session_id in self._sessions:
            del self._sessions[session_id]


# Global memory manager instance
memory_manager = MemoryManager()


def get_conversation_memory(session_id: str = "default") -> ConversationMemory:
    """Convenience function to get conversation memory"""
    return memory_manager.get_session(session_id)
