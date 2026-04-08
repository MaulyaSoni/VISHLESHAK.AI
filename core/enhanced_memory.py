"""
Enhanced Memory Manager - Multi-Tiered Memory System
Main orchestrator for LSTM-like memory with importance weighting
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from core.importance_scorer import get_importance_scorer, ImportanceScorer
from core.memory_consolidation import get_memory_consolidator, MemoryConsolidator
from core.memory_database import get_memory_database, MemoryDatabase
from rag.vector_store import get_vector_store, VectorStoreManager
from config import memory_config
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)


class EnhancedMemoryManager:
    """
    Multi-Tiered Memory System with LSTM-like characteristics
    
    Memory Tiers:
    1. SHORT-TERM: Last N messages (immediate context)
    2. WORKING MEMORY: Summarized recent conversation
    3. LONG-TERM: All conversations in vector DB
    4. SEMANTIC: Extracted facts and preferences
    5. EPISODIC: Important conversation moments
    
    Features:
    - Importance-weighted storage and retrieval
    - Automatic consolidation (like sleep)
    - Selective forgetting
    - Access-based reinforcement
    
    Usage:
        memory = EnhancedMemoryManager(user_id="user123", session_id="session456")
        memory.add_turn(user_msg, bot_response)
        context = memory.retrieve_context(question)
    """
    
    def __init__(
        self,
        user_id: str = "default_user",
        session_id: Optional[str] = None
    ):
        """
        Initialize enhanced memory manager
        
        Args:
            user_id: Unique user identifier
            session_id: Session identifier (generated if not provided)
        """
        self.user_id = user_id
        self.session_id = session_id or self._generate_session_id()
        
        # Initialize components
        self.importance_scorer = get_importance_scorer()
        self.consolidator = get_memory_consolidator()
        self.database = get_memory_database()
        self.vector_store = get_vector_store()
        
        # Initialize memory tiers
        self._init_memory_tiers()
        
        # Statistics tracking
        self.stats = defaultdict(int)
        
        # Consolidation tracking
        self.last_consolidation = datetime.now()
        self.messages_since_consolidation = 0
        
        logger.info(f"✅ Enhanced memory manager initialized for user: {user_id}, session: {session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _init_memory_tiers(self):
        """Initialize all memory tiers"""
        
        # TIER 1: SHORT-TERM MEMORY (Buffer)
        if memory_config.ENABLE_SHORT_TERM_MEMORY:
            self.short_term = ConversationBufferWindowMemory(
                k=memory_config.SHORT_TERM_WINDOW,
                return_messages=True,
                memory_key="chat_history"
            )
            logger.debug("Short-term memory initialized")
        else:
            self.short_term = None
        
        # TIER 2: WORKING MEMORY (Summary)
        if memory_config.ENABLE_WORKING_MEMORY:
            self.working_memory_summary = None
            self.working_memory_messages = []
            logger.debug("Working memory initialized")
        
        # TIER 3, 4, 5: Handled by database and vector store
        # (Long-term, Semantic, Episodic)
    
    # ========================================================================
    # CORE METHODS - ADD & RETRIEVE
    # ========================================================================
    
    def add_turn(
        self,
        user_message: str,
        bot_response: str,
        topic: Optional[str] = None,
        user_feedback: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, int]:
        """
        Add conversation turn to ALL memory tiers
        
        This is the main entry point for storing conversations.
        Implements "write to all, read selectively" strategy.
        
        Args:
            user_message: User's message
            bot_response: Bot's response
            topic: Detected topic (auto-detected if None)
            user_feedback: Optional feedback (1-5 or -1/1)
            metadata: Additional metadata
            
        Returns:
            Dict with message IDs from each tier
        """
        message_ids = {}
        
        # Calculate importance scores
        user_importance = self.importance_scorer.calculate_importance(
            user_message,
            message_type="human",
            user_feedback=user_feedback
        )
        
        bot_importance = self.importance_scorer.calculate_importance(
            bot_response,
            message_type="ai"
        )
        
        # Auto-detect topic if not provided
        if topic is None and memory_config.ENABLE_TOPIC_DETECTION:
            topic = self._detect_topic(user_message)
        
        # TIER 1: SHORT-TERM MEMORY
        if self.short_term:
            self.short_term.chat_memory.add_user_message(user_message)
            self.short_term.chat_memory.add_ai_message(bot_response)
            logger.debug("Added to short-term memory")
        
        # TIER 2: WORKING MEMORY
        if memory_config.ENABLE_WORKING_MEMORY:
            self.working_memory_messages.append({
                "type": "human",
                "content": user_message,
                "importance": user_importance
            })
            self.working_memory_messages.append({
                "type": "ai",
                "content": bot_response,
                "importance": bot_importance
            })
            
            # Update summary if needed
            if self._should_update_working_memory():
                self._update_working_memory()
        
        # TIER 3: LONG-TERM MEMORY (Database + Vector Store)
        if memory_config.ENABLE_LONG_TERM_MEMORY:
            # Save to database
            user_msg_id = self.database.save_conversation(
                session_id=self.session_id,
                user_id=self.user_id,
                message_type="human",
                message=user_message,
                importance_score=user_importance,
                topic=topic,
                metadata=metadata
            )
            
            bot_msg_id = self.database.save_conversation(
                session_id=self.session_id,
                user_id=self.user_id,
                message_type="ai",
                message=bot_response,
                importance_score=bot_importance,
                topic=topic,
                metadata=metadata
            )
            
            message_ids['database'] = (user_msg_id, bot_msg_id)
            
            # Save to vector store for semantic search
            conversation_text = f"User: {user_message}\n\nAssistant: {bot_response}"
            
            vector_id = self.vector_store.save_analysis(
                analysis_text=conversation_text,
                metadata={
                    "session_id": self.session_id,
                    "user_id": self.user_id,
                    "timestamp": datetime.now().isoformat(),
                    "importance": (user_importance + bot_importance) / 2,
                    "topic": topic,
                    "message_ids": [user_msg_id, bot_msg_id]
                }
            )
            
            message_ids['vector_store'] = vector_id
            logger.debug(f"Added to long-term memory: {vector_id}")
        
        # Update statistics
        self.stats['messages_added'] += 2
        self.messages_since_consolidation += 2
        
        # Check if consolidation needed
        if self._should_consolidate():
            self.consolidate_memories()
        
        logger.info(f"Turn added successfully. Importance: user={user_importance:.2f}, bot={bot_importance:.2f}")
        
        return message_ids
    
    def retrieve_context(
        self,
        query: str,
        strategy: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Retrieve context from all relevant memory tiers (LSTM-like gating)
        
        This implements selective retrieval based on query characteristics.
        
        Args:
            query: User's current question
            strategy: Retrieval strategy ('conservative', 'aggressive', 'hybrid')
            
        Returns:
            Dict with context from all tiers
        """
        strategy_config = memory_config.CONTEXT_STRATEGIES.get(
            strategy,
            memory_config.CURRENT_STRATEGY
        )
        
        context = {}
        
        # TIER 1: SHORT-TERM MEMORY (always included)
        if self.short_term:
            context['short_term'] = self.short_term.load_memory_variables({})
            logger.debug(f"Retrieved {len(context['short_term'].get('chat_history', []))} short-term messages")
        
        # TIER 2: WORKING MEMORY (summary)
        if memory_config.ENABLE_WORKING_MEMORY and self.working_memory_summary:
            context['working_memory'] = {
                "summary": self.working_memory_summary,
                "message_count": len(self.working_memory_messages)
            }
            logger.debug("Retrieved working memory summary")
        
        # TIER 3: LONG-TERM MEMORY (selective retrieval)
        if self._needs_long_term_context(query):
            long_term_context = self._retrieve_long_term(
                query,
                k=strategy_config['long_term_k']
            )
            context['long_term'] = long_term_context
            logger.debug(f"Retrieved {len(long_term_context)} long-term memories")
        
        # TIER 4: SEMANTIC MEMORY (facts and preferences)
        if memory_config.ENABLE_SEMANTIC_MEMORY:
            semantic_context = self._retrieve_semantic(
                k=strategy_config['semantic_k']
            )
            context['semantic'] = semantic_context
            logger.debug(f"Retrieved {len(semantic_context)} semantic memories")
        
        # TIER 5: EPISODIC MEMORY (important moments)
        if self._needs_episodic_context(query):
            episodic_context = self._retrieve_episodic(
                query,
                k=strategy_config['episodic_k']
            )
            context['episodic'] = episodic_context
            logger.debug(f"Retrieved {len(episodic_context)} episodic memories")
        
        # Update statistics
        self.stats['context_retrievals'] += 1
        
        return context
    
    # ========================================================================
    # TIER 2: WORKING MEMORY METHODS
    # ========================================================================
    
    def _should_update_working_memory(self) -> bool:
        """Check if working memory summary should be updated"""
        return (
            len(self.working_memory_messages) >= 
            memory_config.WORKING_MEMORY_UPDATE_FREQUENCY
        )
    
    def _update_working_memory(self):
        """Update working memory summary"""
        if not self.working_memory_messages:
            return
        
        logger.info("Updating working memory summary...")
        
        # Create summary
        self.working_memory_summary = self.consolidator.create_summary(
            messages=self.working_memory_messages,
            existing_summary=self.working_memory_summary
        )
        
        # Save to database
        if len(self.working_memory_messages) >= 2:
            window_start = self.working_memory_messages[0].get('message_id', 0)
            window_end = self.working_memory_messages[-1].get('message_id', 0)
            
            # Calculate compression ratio
            original_text = " ".join(m['content'] for m in self.working_memory_messages)
            compression_ratio = self.consolidator.calculate_compression_ratio(
                original_text,
                self.working_memory_summary
            )
            
            self.database.save_working_memory(
                session_id=self.session_id,
                user_id=self.user_id,
                summary_text=self.working_memory_summary,
                window_start=window_start,
                window_end=window_end,
                message_count=len(self.working_memory_messages),
                compression_ratio=compression_ratio
            )
        
        # Keep only recent messages in buffer
        if len(self.working_memory_messages) > memory_config.WORKING_MEMORY_WINDOW:
            self.working_memory_messages = self.working_memory_messages[-memory_config.WORKING_MEMORY_WINDOW:]
        
        logger.info(f"Working memory updated. Summary length: {len(self.working_memory_summary)} chars")
    
    # ========================================================================
    # TIER 3: LONG-TERM MEMORY METHODS
    # ========================================================================
    
    def _needs_long_term_context(self, query: str) -> bool:
        """Determine if query needs long-term context"""
        # Keywords that suggest historical context is needed
        historical_keywords = [
            'previous', 'last time', 'before', 'earlier', 'ago',
            'remember', 'recall', 'we discussed', 'you said',
            'compare', 'difference', 'change', 'trend'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in historical_keywords)
    
    def _retrieve_long_term(self, query: str, k: int = 5) -> List[Dict]:
        """
        Retrieve from long-term memory (vector store + database)
        
        Uses importance-weighted retrieval
        """
        # Retrieve from vector store (semantic similarity)
        similar_conversations = self.vector_store.retrieve_similar_analyses(
            query=query,
            k=k,
            filter_metadata={"user_id": self.user_id}
        )
        
        # Get full details from database and calculate retrieval scores
        enriched_results = []
        
        for conv in similar_conversations:
            # Calculate age
            timestamp = conv['metadata'].get('timestamp')
            if timestamp:
                age = (datetime.now() - datetime.fromisoformat(timestamp)).days
                recency_score = self.importance_scorer.calculate_recency_score(age)
            else:
                recency_score = 0.5
            
            # Calculate final retrieval score
            retrieval_score = self.importance_scorer.calculate_retrieval_score(
                importance=conv['metadata'].get('importance', 0.5),
                similarity=conv['similarity'],
                recency=recency_score
            )
            
            enriched_results.append({
                "text": conv['text'],
                "metadata": conv['metadata'],
                "similarity": conv['similarity'],
                "retrieval_score": retrieval_score
            })
        
        # Sort by retrieval score
        enriched_results.sort(key=lambda x: x['retrieval_score'], reverse=True)
        
        return enriched_results[:k]
    
    # ========================================================================
    # TIER 4: SEMANTIC MEMORY METHODS
    # ========================================================================
    
    def _retrieve_semantic(self, k: int = 5) -> List[Dict]:
        """Retrieve semantic memories (facts, preferences)"""
        memories = self.database.get_semantic_memories(
            user_id=self.user_id,
            min_confidence=memory_config.SEMANTIC_CONFIDENCE_THRESHOLD
        )
        
        # Update access counts
        for memory in memories[:k]:
            self.database.increment_semantic_access(memory['id'])
        
        return memories[:k]
    
    def extract_and_save_semantic(self, messages: List[Dict]):
        """Extract semantic knowledge from messages and save"""
        if not memory_config.EXTRACT_USER_PREFERENCES:
            return
        
        # Extract knowledge
        knowledge = self.consolidator.extract_semantic_knowledge(messages)
        
        # Save preferences
        for pref in knowledge.get('user_preferences', []):
            self.database.save_semantic_memory(
                user_id=self.user_id,
                memory_type='preference',
                key=f"preference.{pref['preference']}",
                value=pref['preference'],
                confidence=pref.get('confidence', 0.5),
                source='conversation_extraction'
            )
        
        # Save facts
        for fact in knowledge.get('facts_learned', []):
            self.database.save_semantic_memory(
                user_id=self.user_id,
                memory_type='fact',
                key=f"fact.{fact['fact'][:50]}",
                value=fact['fact'],
                confidence=fact.get('confidence', 0.5),
                source='conversation_extraction'
            )
        
        # Save insights
        for insight in knowledge.get('insights', []):
            self.database.save_semantic_memory(
                user_id=self.user_id,
                memory_type='insight',
                key=f"insight.{insight['insight'][:50]}",
                value=insight['insight'],
                confidence=insight.get('importance', 0.5),
                source='conversation_extraction'
            )
        
        logger.info(f"Extracted and saved semantic knowledge: "
                   f"{len(knowledge.get('user_preferences', []))} preferences, "
                   f"{len(knowledge.get('facts_learned', []))} facts")
    
    # ========================================================================
    # TIER 5: EPISODIC MEMORY METHODS
    # ========================================================================
    
    def _needs_episodic_context(self, query: str) -> bool:
        """Determine if query needs episodic context"""
        episodic_keywords = [
            'when we', 'that time', 'breakthrough', 'discovered',
            'realized', 'found out', 'important moment'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in episodic_keywords)
    
    def _retrieve_episodic(self, query: str, k: int = 3) -> List[Dict]:
        """Retrieve episodic memories"""
        episodes = self.database.get_episodic_memories(
            user_id=self.user_id,
            limit=k,
            min_importance=memory_config.EPISODIC_IMPORTANCE_THRESHOLD
        )
        
        return episodes
    
    def identify_and_save_episodes(self):
        """Identify and save episodic memories from recent conversations"""
        if not memory_config.ENABLE_EPISODIC_MEMORY:
            return
        
        # Get recent high-importance messages
        recent_messages = self.database.get_conversation_history(
            session_id=self.session_id,
            limit=50,
            min_importance=0.7
        )
        
        if not recent_messages:
            return
        
        # Identify episodes
        episodes = self.consolidator.identify_episodes(
            messages=recent_messages,
            importance_threshold=memory_config.EPISODIC_IMPORTANCE_THRESHOLD
        )
        
        # Save episodes
        for episode in episodes:
            # Create episode summary
            episode_messages = episode['messages']
            episode_text = "\n\n".join(
                f"{m['message_type']}: {m['message']}" 
                for m in episode_messages
            )
            
            # Generate summary
            summary = self.consolidator.create_summary(
                messages=[
                    {"type": m['message_type'], "content": m['message']}
                    for m in episode_messages
                ]
            )
            
            # Save to database
            self.database.save_episodic_memory(
                session_id=self.session_id,
                user_id=self.user_id,
                episode_summary=summary,
                full_context=episode_text,
                importance_score=episode['avg_importance'],
                episode_type='auto_detected',
                tags=['high_importance', 'conversation'],
                message_ids=[m['id'] for m in episode_messages]
            )
        
        logger.info(f"Identified and saved {len(episodes)} episodic memories")
    
    # ========================================================================
    # CONSOLIDATION & MAINTENANCE
    # ========================================================================
    
    def _should_consolidate(self) -> bool:
        """Check if consolidation should run"""
        if not memory_config.CONSOLIDATION_ENABLED:
            return False
        
        # Check message threshold
        if self.messages_since_consolidation >= memory_config.CONSOLIDATION_MESSAGE_THRESHOLD:
            return True
        
        # Check time threshold
        time_since = datetime.now() - self.last_consolidation
        if time_since >= memory_config.CONSOLIDATION_FREQUENCY:
            return True
        
        return False
    
    def consolidate_memories(self):
        """
        Consolidate memories (like sleep consolidation in brain)
        
        Operations:
        1. Update working memory summaries
        2. Extract semantic knowledge
        3. Identify episodic memories
        4. Apply decay to old memories
        5. Clean up low-importance memories
        """
        logger.info("🔄 Starting memory consolidation...")
        start_time = datetime.now()
        
        stats = {
            'messages_processed': 0,
            'summaries_created': 0,
            'semantic_extracted': 0,
            'episodes_created': 0,
            'memories_cleaned': 0
        }
        
        try:
            # 1. Update working memory
            if memory_config.CONSOLIDATE_SUMMARIES:
                if self.working_memory_messages:
                    self._update_working_memory()
                    stats['summaries_created'] += 1
            
            # 2. Extract semantic knowledge
            if memory_config.CONSOLIDATE_SEMANTIC:
                recent_messages = self.database.get_conversation_history(
                    session_id=self.session_id,
                    limit=50
                )
                
                if len(recent_messages) >= 10:
                    formatted_messages = [
                        {"type": m['message_type'], "content": m['message']}
                        for m in recent_messages
                    ]
                    self.extract_and_save_semantic(formatted_messages)
                    stats['semantic_extracted'] += 1
            
            # 3. Identify episodic memories
            self.identify_and_save_episodes()
            
            # 4. Apply memory decay
            if memory_config.ENABLE_MEMORY_DECAY:
                self._apply_memory_decay()
            
            # 5. Clean up (selective forgetting)
            if memory_config.CONSOLIDATE_CLEANUP:
                deleted = self._cleanup_memories()
                stats['memories_cleaned'] = deleted
            
            # Reset counters
            self.last_consolidation = datetime.now()
            self.messages_since_consolidation = 0
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Consolidation complete in {processing_time:.2f}s. Stats: {stats}")
        
        except Exception as e:
            logger.error(f"Error during consolidation: {e}", exc_info=True)
    
    def _apply_memory_decay(self):
        """Apply temporal decay to memory importance scores"""
        # This would update decay_factor in database
        # For now, decay is applied during retrieval
        pass
    
    def _cleanup_memories(self) -> int:
        """Clean up low-importance old memories"""
        if not memory_config.FORGETTING_ENABLED:
            return 0
        
        deleted_count = self.database.delete_old_conversations(
            days=memory_config.FORGETTING_MIN_AGE_DAYS,
            min_importance=memory_config.FORGETTING_THRESHOLD
        )
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} low-importance memories")
        
        return deleted_count
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _detect_topic(self, message: str) -> str:
        """Auto-detect conversation topic"""
        # Simple keyword-based detection
        message_lower = message.lower()
        
        topics = {
            'analysis': ['analyze', 'analysis', 'statistical', 'correlation'],
            'visualization': ['chart', 'plot', 'graph', 'visualize'],
            'data_quality': ['missing', 'null', 'outlier', 'clean'],
            'export': ['export', 'download', 'save', 'file'],
            'comparison': ['compare', 'difference', 'versus', 'vs'],
        }
        
        for topic, keywords in topics.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic
        
        return 'general'
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format retrieved context for LLM prompt
        
        Args:
            context: Context dict from retrieve_context()
            
        Returns:
            Formatted string for prompt
        """
        parts = []
        
        # Short-term memory (recent conversation)
        if 'short_term' in context and context['short_term'].get('chat_history'):
            parts.append("RECENT CONVERSATION:")
            for msg in context['short_term']['chat_history'][-5:]:  # Last 5
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                parts.append(f"{role}: {msg.content[:200]}...")
            parts.append("")
        
        # Working memory (summary)
        if 'working_memory' in context:
            parts.append("CONVERSATION SUMMARY:")
            parts.append(context['working_memory']['summary'][:500])
            parts.append("")
        
        # Long-term memory (relevant history)
        if 'long_term' in context and context['long_term']:
            parts.append("RELEVANT PAST CONVERSATIONS:")
            for i, conv in enumerate(context['long_term'][:3], 1):
                parts.append(f"{i}. {conv['text'][:300]}...")
            parts.append("")
        
        # Semantic memory (facts & preferences)
        if 'semantic' in context and context['semantic']:
            parts.append("KNOWN FACTS & PREFERENCES:")
            for mem in context['semantic'][:5]:
                parts.append(f"- {mem['value']}")
            parts.append("")
        
        # Episodic memory (important moments)
        if 'episodic' in context and context['episodic']:
            parts.append("IMPORTANT PAST MOMENTS:")
            for ep in context['episodic'][:2]:
                parts.append(f"- {ep['episode_summary'][:200]}...")
            parts.append("")
        
        return "\n".join(parts)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        db_stats = self.database.get_statistics()
        
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "operations": dict(self.stats),
            "database": db_stats,
            "short_term_size": len(self.short_term.chat_memory.messages) if self.short_term else 0,
            "working_memory_size": len(self.working_memory_messages),
            "last_consolidation": self.last_consolidation.isoformat(),
            "messages_since_consolidation": self.messages_since_consolidation
        }
    
    def clear_session(self):
        """Clear current session (keep long-term memory)"""
        if self.short_term:
            self.short_term.clear()
        
        self.working_memory_messages = []
        self.working_memory_summary = None
        self.messages_since_consolidation = 0
        
        logger.info("Session cleared (long-term memory preserved)")
    
    def clear_all_memory(self):
        """Clear ALL memory for this user (destructive!)"""
        # This would delete everything from database
        # Use with caution!
        logger.warning(f"Clearing all memory for user: {self.user_id}")
        # Implementation would go here


# Global instances per user/session
_memory_managers = {}

def get_enhanced_memory_manager(
    user_id: str = "default_user",
    session_id: Optional[str] = None
) -> EnhancedMemoryManager:
    """
    Get or create enhanced memory manager for user/session
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        EnhancedMemoryManager instance
    """
    key = f"{user_id}:{session_id or 'default'}"
    
    if key not in _memory_managers:
        _memory_managers[key] = EnhancedMemoryManager(user_id, session_id)
    
    return _memory_managers[key]
