"""
Enhanced Memory Database Manager
Handles all SQLite operations for memory system
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging
from config import memory_config

logger = logging.getLogger(__name__)


class MemoryDatabase:
    """
    Manages SQLite database for enhanced memory system
    
    Features:
    - All CRUD operations for memory tables
    - Optimized queries with indexes
    - Transaction support
    - Connection pooling
    
    Usage:
        db = MemoryDatabase()
        db.save_conversation(session_id, message_type, message)
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize memory database
        
        Args:
            db_path: Path to database file (default from config)
        """
        self.db_path = db_path or memory_config.MEMORY_DB_PATH
        self._init_database()
        logger.info(f"✅ Memory database initialized: {self.db_path}")
    
    def _init_database(self):
        """Initialize database with schema"""
        # Create directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load and execute schema
        schema_path = memory_config.SCHEMA_PATH
        
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            conn = self._get_connection()
            try:
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Database schema initialized")
            except Exception as e:
                logger.error(f"Error initializing schema: {e}")
                raise
            finally:
                conn.close()
        else:
            logger.warning(f"Schema file not found: {schema_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        return conn
    
    # ========================================================================
    # CONVERSATIONS TABLE
    # ========================================================================
    
    def save_conversation(
        self,
        session_id: str,
        user_id: str,
        message_type: str,
        message: str,
        importance_score: float = 0.5,
        topic: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Save conversation message
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            message_type: 'human' or 'ai'
            message: Message content
            importance_score: Importance score (0-1)
            topic: Detected topic
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO conversations (
                    session_id, user_id, message_type, message,
                    importance_score, topic, metadata, token_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                message_type,
                message,
                importance_score,
                topic,
                json.dumps(metadata) if metadata else None,
                len(message.split())
            ))
            
            conn.commit()
            message_id = cursor.lastrowid
            
            logger.debug(f"Saved conversation message: {message_id}")
            return message_id
        
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_conversation_history(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        min_importance: Optional[float] = None
    ) -> List[Dict]:
        """
        Get conversation history
        
        Args:
            session_id: Filter by session (optional)
            user_id: Filter by user (optional)
            limit: Maximum messages to return
            min_importance: Minimum importance score
            
        Returns:
            List of message dicts
        """
        conn = self._get_connection()
        try:
            query = "SELECT * FROM conversations WHERE 1=1"
            params = []
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if min_importance:
                query += " AND importance_score >= ?"
                params.append(min_importance)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        
        finally:
            conn.close()
    
    def update_message_importance(
        self,
        message_id: int,
        new_importance: float,
        decay_factor: Optional[float] = None
    ):
        """Update importance score for a message"""
        conn = self._get_connection()
        try:
            if decay_factor is not None:
                conn.execute("""
                    UPDATE conversations
                    SET importance_score = ?, decay_factor = ?
                    WHERE id = ?
                """, (new_importance, decay_factor, message_id))
            else:
                conn.execute("""
                    UPDATE conversations
                    SET importance_score = ?
                    WHERE id = ?
                """, (new_importance, message_id))
            
            conn.commit()
        finally:
            conn.close()
    
    def increment_access_count(self, message_id: int):
        """Increment access count when message is retrieved"""
        conn = self._get_connection()
        try:
            conn.execute("""
                UPDATE conversations
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (message_id,))
            conn.commit()
        finally:
            conn.close()
    
    def delete_old_conversations(
        self,
        days: int,
        min_importance: float = 0.0
    ) -> int:
        """
        Delete old conversations below importance threshold
        
        Args:
            days: Delete messages older than this
            min_importance: Only delete if importance below this
            
        Returns:
            Number of deleted messages
        """
        conn = self._get_connection()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor = conn.execute("""
                DELETE FROM conversations
                WHERE timestamp < ?
                AND importance_score < ?
            """, (cutoff_date, min_importance))
            
            conn.commit()
            deleted_count = cursor.rowcount
            
            logger.info(f"Deleted {deleted_count} old conversations")
            return deleted_count
        
        finally:
            conn.close()
    
    # ========================================================================
    # WORKING MEMORY TABLE
    # ========================================================================
    
    def save_working_memory(
        self,
        session_id: str,
        user_id: str,
        summary_text: str,
        window_start: int,
        window_end: int,
        message_count: int,
        compression_ratio: float
    ) -> int:
        """Save working memory summary"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO working_memory (
                    session_id, user_id, summary_text,
                    window_start, window_end, message_count,
                    compression_ratio
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, user_id, summary_text,
                window_start, window_end, message_count,
                compression_ratio
            ))
            
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_working_memory(
        self,
        session_id: str
    ) -> Optional[Dict]:
        """Get most recent working memory for session"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM working_memory
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (session_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    # ========================================================================
    # SEMANTIC MEMORY TABLE
    # ========================================================================
    
    def save_semantic_memory(
        self,
        user_id: str,
        memory_type: str,
        key: str,
        value: str,
        confidence: float = 0.5,
        source: Optional[str] = None
    ) -> int:
        """
        Save semantic memory (fact, preference, insight, rule)
        
        Uses INSERT OR REPLACE to update existing memories
        """
        conn = self._get_connection()
        try:
            # Check if exists
            cursor = conn.execute("""
                SELECT id, evidence_count FROM semantic_memory
                WHERE user_id = ? AND key = ?
            """, (user_id, key))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                new_evidence = existing['evidence_count'] + 1
                conn.execute("""
                    UPDATE semantic_memory
                    SET value = ?,
                        confidence = ?,
                        source = ?,
                        evidence_count = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (value, confidence, source, new_evidence, existing['id']))
                
                memory_id = existing['id']
            else:
                # Insert new
                cursor = conn.execute("""
                    INSERT INTO semantic_memory (
                        user_id, memory_type, key, value,
                        confidence, source
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, memory_type, key, value, confidence, source))
                
                memory_id = cursor.lastrowid
            
            conn.commit()
            return memory_id
        
        finally:
            conn.close()
    
    def get_semantic_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        min_confidence: float = 0.6
    ) -> List[Dict]:
        """Get semantic memories for user"""
        conn = self._get_connection()
        try:
            query = """
                SELECT * FROM semantic_memory
                WHERE user_id = ?
                AND confidence >= ?
            """
            params = [user_id, min_confidence]
            
            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type)
            
            query += " ORDER BY confidence DESC, last_updated DESC"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def increment_semantic_access(self, memory_id: int):
        """Increment access count for semantic memory"""
        conn = self._get_connection()
        try:
            conn.execute("""
                UPDATE semantic_memory
                SET access_count = access_count + 1
                WHERE id = ?
            """, (memory_id,))
            conn.commit()
        finally:
            conn.close()
    
    # ========================================================================
    # EPISODIC MEMORY TABLE
    # ========================================================================
    
    def save_episodic_memory(
        self,
        session_id: str,
        user_id: str,
        episode_summary: str,
        full_context: str,
        importance_score: float,
        episode_type: str,
        tags: List[str],
        message_ids: List[int]
    ) -> int:
        """Save episodic memory"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO episodic_memory (
                    session_id, user_id, episode_summary,
                    full_context, importance_score, episode_type,
                    tags, message_ids
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, user_id, episode_summary,
                full_context, importance_score, episode_type,
                json.dumps(tags), json.dumps(message_ids)
            ))
            
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_episodic_memories(
        self,
        user_id: str,
        limit: int = 10,
        min_importance: float = 0.8
    ) -> List[Dict]:
        """Get episodic memories for user"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM episodic_memory
                WHERE user_id = ?
                AND importance_score >= ?
                ORDER BY importance_score DESC, created_at DESC
                LIMIT ?
            """, (user_id, min_importance, limit))
            
            rows = cursor.fetchall()
            
            # Parse JSON fields
            results = []
            for row in rows:
                row_dict = dict(row)
                row_dict['tags'] = json.loads(row_dict['tags'])
                row_dict['message_ids'] = json.loads(row_dict['message_ids'])
                results.append(row_dict)
            
            return results
        finally:
            conn.close()
    
    # ========================================================================
    # USER PREFERENCES TABLE
    # ========================================================================
    
    def save_user_preference(
        self,
        user_id: str,
        preference_category: str,
        preference_key: str,
        preference_value: str,
        learned_from: str = "implicit",
        confidence: float = 0.5
    ):
        """Save user preference"""
        conn = self._get_connection()
        try:
            # Check if exists
            cursor = conn.execute("""
                SELECT id, evidence_count FROM user_preferences
                WHERE user_id = ?
                AND preference_category = ?
                AND preference_key = ?
            """, (user_id, preference_category, preference_key))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                new_evidence = existing['evidence_count'] + 1
                conn.execute("""
                    UPDATE user_preferences
                    SET preference_value = ?,
                        confidence = ?,
                        evidence_count = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (preference_value, confidence, new_evidence, existing['id']))
            else:
                # Insert new
                conn.execute("""
                    INSERT INTO user_preferences (
                        user_id, preference_category, preference_key,
                        preference_value, learned_from, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, preference_category, preference_key,
                     preference_value, learned_from, confidence))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_user_preferences(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Get user preferences"""
        conn = self._get_connection()
        try:
            if category:
                cursor = conn.execute("""
                    SELECT * FROM user_preferences
                    WHERE user_id = ? AND preference_category = ?
                    ORDER BY confidence DESC
                """, (user_id, category))
            else:
                cursor = conn.execute("""
                    SELECT * FROM user_preferences
                    WHERE user_id = ?
                    ORDER BY preference_category, confidence DESC
                """, (user_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    # ========================================================================
    # FEEDBACK LOG TABLE
    # ========================================================================
    
    def save_feedback(
        self,
        session_id: str,
        user_id: str,
        message_id: int,
        feedback_type: str,
        feedback_value: int,
        feedback_text: Optional[str] = None,
        question_text: Optional[str] = None,
        response_text: Optional[str] = None
    ):
        """Save user feedback"""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO feedback_log (
                    session_id, user_id, message_id,
                    feedback_type, feedback_value, feedback_text,
                    question_text, response_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, user_id, message_id,
                feedback_type, feedback_value, feedback_text,
                question_text, response_text
            ))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_feedback_stats(self, user_id: str) -> Dict:
        """Get feedback statistics for user"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_feedback,
                    SUM(CASE WHEN feedback_value > 0 THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN feedback_value < 0 THEN 1 ELSE 0 END) as negative,
                    AVG(CASE WHEN feedback_type = 'rating' THEN feedback_value END) as avg_rating
                FROM feedback_log
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        conn = self._get_connection()
        try:
            stats = {}
            
            # Conversation stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(DISTINCT user_id) as total_users,
                    AVG(importance_score) as avg_importance
                FROM conversations
            """)
            stats['conversations'] = dict(cursor.fetchone())
            
            # Semantic memory stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_memories,
                    COUNT(DISTINCT user_id) as users_with_memories,
                    AVG(confidence) as avg_confidence
                FROM semantic_memory
            """)
            stats['semantic'] = dict(cursor.fetchone())
            
            # Episodic memory stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_episodes,
                    AVG(importance_score) as avg_importance
                FROM episodic_memory
            """)
            stats['episodic'] = dict(cursor.fetchone())
            
            return stats
        finally:
            conn.close()
    
    def vacuum(self):
        """Vacuum database to reclaim space"""
        conn = self._get_connection()
        try:
            conn.execute("VACUUM")
            logger.info("Database vacuumed")
        finally:
            conn.close()


# Global instance
_memory_database = None

def get_memory_database() -> MemoryDatabase:
    """Get global memory database instance"""
    global _memory_database
    if _memory_database is None:
        _memory_database = MemoryDatabase()
    return _memory_database
