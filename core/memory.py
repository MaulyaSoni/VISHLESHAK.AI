"""
Chat Memory Management for FINBOT v4
Persistent conversation history using SQLite

Features:
- SQLite-based storage
- Conversation buffer memory
- Session management
- Message history persistence
- Context window management
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import settings


class ChatMemoryManager:
    """
    Manages persistent chat memory using SQLite database
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize memory manager
        
        Args:
            db_path: Path to SQLite database (defaults to settings.CHAT_HISTORY_DB)
        """
        self.db_path = db_path or settings.CHAT_HISTORY_DB
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        # Create directory if needed
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Create tables
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    message_type TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_messages 
                ON messages(session_id, timestamp)
            """)
            
            conn.commit()
    
    def create_session(self, session_id: str, metadata: Optional[Dict] = None):
        """
        Create a new chat session
        
        Args:
            session_id: Unique session identifier
            metadata: Optional metadata to store with session
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO sessions (session_id, metadata)
                VALUES (?, ?)
            """, (session_id, json.dumps(metadata or {})))
            
            conn.commit()
    
    def add_message(self, session_id: str, message_type: str, content: str, 
                    metadata: Optional[Dict] = None):
        """
        Add a message to the conversation history
        
        Args:
            session_id: Session identifier
            message_type: 'human' or 'ai'
            content: Message content
            metadata: Optional message metadata
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Ensure session exists
            self.create_session(session_id)
            
            # Add message
            cursor.execute("""
                INSERT INTO messages (session_id, message_type, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (session_id, message_type, content, json.dumps(metadata or {})))
            
            # Update session last_active
            cursor.execute("""
                UPDATE sessions 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
    
    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get messages for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve (most recent)
        
        Returns:
            List of message dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT message_type, content, timestamp, metadata
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'type': row[0],
                    'content': row[1],
                    'timestamp': row[2],
                    'metadata': json.loads(row[3]) if row[3] else {}
                })
            
            return messages
    
    def get_recent_messages(self, session_id: str, n: int = None) -> List[Dict[str, Any]]:
        """
        Get the N most recent messages
        
        Args:
            session_id: Session identifier
            n: Number of messages (defaults to CHAT_MEMORY_WINDOW)
        
        Returns:
            List of recent messages
        """
        n = n or settings.CHAT_MEMORY_WINDOW
        
        messages = self.get_messages(session_id)
        return messages[-n:] if len(messages) > n else messages
    
    def clear_session(self, session_id: str):
        """
        Clear all messages for a session
        
        Args:
            session_id: Session identifier
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            
            conn.commit()
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all chat sessions
        
        Returns:
            List of session information
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, created_at, last_active, metadata
                FROM sessions
                ORDER BY last_active DESC
            """)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'created_at': row[1],
                    'last_active': row[2],
                    'metadata': json.loads(row[3]) if row[3] else {}
                })
            
            return sessions
    
    def get_memory_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get memory context for the session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary with chat history and metadata
        """
        messages = self.get_recent_messages(session_id)
        
        return {
            'chat_history': messages,
            'window_size': settings.CHAT_MEMORY_WINDOW,
            'total_messages': len(messages)
        }
    
    def save_to_memory(self, session_id: str, human_message: str, ai_message: str):
        """
        Save a conversation exchange
        
        Args:
            session_id: Session identifier
            human_message: User's message
            ai_message: AI's response
        """
        self.add_message(session_id, 'human', human_message)
        self.add_message(session_id, 'ai', ai_message)
    
    def get_conversation_summary(self, session_id: str) -> str:
        """
        Get a summary of the conversation
        
        Args:
            session_id: Session identifier
        
        Returns:
            Summary string
        """
        messages = self.get_messages(session_id)
        
        if not messages:
            return "No conversation history."
        
        human_count = sum(1 for m in messages if m['type'] == 'human')
        ai_count = sum(1 for m in messages if m['type'] == 'ai')
        
        first_msg = messages[0]['timestamp']
        last_msg = messages[-1]['timestamp']
        
        return (
            f"Conversation has {len(messages)} messages "
            f"({human_count} from user, {ai_count} from AI). "
            f"Started: {first_msg}, Last: {last_msg}"
        )


class ConversationManager:
    """
    High-level conversation manager that combines memory and LLM
    """
    
    def __init__(self, session_id: str):
        """
        Initialize conversation manager
        
        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.memory_manager = ChatMemoryManager()
        self.memory_manager.create_session(session_id)
    
    def add_exchange(self, user_message: str, ai_response: str):
        """Add a conversation exchange"""
        self.memory_manager.save_to_memory(self.session_id, user_message, ai_response)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.memory_manager.get_messages(self.session_id)
    
    def clear(self):
        """Clear conversation history"""
        self.memory_manager.clear_session(self.session_id)
    
    def get_memory(self) -> Dict[str, Any]:
        """Get memory context as dictionary"""
        return self.memory_manager.get_memory_context(self.session_id)
