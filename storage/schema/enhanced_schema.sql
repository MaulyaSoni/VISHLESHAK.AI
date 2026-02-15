-- ============================================================================
-- FINBOT v4 - Enhanced Memory Schema
-- Supports multi-tiered memory with LSTM-like characteristics
-- ============================================================================

-- 1. CONVERSATIONS (Enhanced from existing)
-- Stores all conversation turns with importance scoring
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT DEFAULT 'default_user',
    message_type TEXT NOT NULL,  -- 'human' or 'ai'
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- NEW: LSTM-like features
    importance_score FLOAT DEFAULT 0.5,  -- 0.0 to 1.0
    decay_factor FLOAT DEFAULT 1.0,      -- Decreases over time
    access_count INTEGER DEFAULT 0,      -- How often retrieved
    last_accessed DATETIME,              -- Last retrieval time
    
    -- NEW: Context features
    topic TEXT,                          -- Auto-detected topic
    intent TEXT,                         -- Question intent
    sentiment TEXT,                      -- Positive/neutral/negative
    
    -- NEW: Metadata
    token_count INTEGER,                 -- Message length in tokens
    metadata TEXT                        -- JSON for additional data
);

CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_importance ON conversations(importance_score);

-- 2. WORKING MEMORY (NEW)
-- Stores compressed summaries of conversation windows
CREATE TABLE IF NOT EXISTS working_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    
    -- Summary content
    summary_text TEXT NOT NULL,
    window_start INTEGER,               -- First message ID in window
    window_end INTEGER,                 -- Last message ID in window
    message_count INTEGER,              -- Messages summarized
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    summary_type TEXT DEFAULT 'auto',   -- 'auto' or 'manual'
    compression_ratio FLOAT             -- Original/summary token ratio
);

CREATE INDEX IF NOT EXISTS idx_session_working ON working_memory(session_id);

-- 3. SEMANTIC MEMORY (NEW)
-- Stores extracted facts, preferences, and learned knowledge
CREATE TABLE IF NOT EXISTS semantic_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    
    -- Memory content
    memory_type TEXT NOT NULL,          -- 'fact', 'preference', 'insight', 'rule'
    key TEXT NOT NULL,                  -- Structured key (e.g., 'user.preference.analysis_style')
    value TEXT NOT NULL,                -- Value or description
    
    -- Confidence and validation
    confidence FLOAT DEFAULT 0.5,       -- 0.0 to 1.0
    source TEXT,                        -- Where this came from
    evidence_count INTEGER DEFAULT 1,   -- Supporting evidence count
    
    -- Temporal features
    first_learned DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_validated DATETIME,
    
    -- Usage tracking (LSTM-like)
    access_count INTEGER DEFAULT 0,
    relevance_score FLOAT DEFAULT 0.5,
    
    UNIQUE (user_id, key)
);

CREATE INDEX IF NOT EXISTS idx_user_semantic ON semantic_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_type ON semantic_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_key ON semantic_memory(key);

-- 4. EPISODIC MEMORY (NEW)
-- Stores important conversation moments and breakthroughs
CREATE TABLE IF NOT EXISTS episodic_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    
    -- Episode content
    episode_summary TEXT NOT NULL,
    full_context TEXT,                  -- Full conversation context
    
    -- Importance features
    importance_score FLOAT NOT NULL,    -- Why this is memorable
    emotional_valence TEXT,             -- 'positive', 'negative', 'breakthrough'
    
    -- Classification
    episode_type TEXT,                  -- 'insight', 'decision', 'preference', 'breakthrough'
    tags TEXT,                          -- JSON array of tags
    
    -- Message references
    message_ids TEXT,                   -- JSON array of message IDs involved
    
    -- Temporal
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Retrieval features
    access_count INTEGER DEFAULT 0,
    last_accessed DATETIME
);

CREATE INDEX IF NOT EXISTS idx_user_episodic ON episodic_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_importance_episodic ON episodic_memory(importance_score);
CREATE INDEX IF NOT EXISTS idx_type_episodic ON episodic_memory(episode_type);

-- 5. USER PREFERENCES (NEW)
-- Stores learned user preferences for RLHF-like behavior
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    
    -- Preference details
    preference_category TEXT NOT NULL,  -- 'response_style', 'analysis', 'visualization', etc.
    preference_key TEXT NOT NULL,
    preference_value TEXT NOT NULL,
    
    -- Learning metadata
    learned_from TEXT NOT NULL,         -- 'explicit', 'implicit', 'feedback'
    confidence FLOAT DEFAULT 0.5,
    evidence_count INTEGER DEFAULT 1,
    
    -- Temporal
    first_learned DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (user_id, preference_category, preference_key)
);

CREATE INDEX IF NOT EXISTS idx_user_pref ON user_preferences(user_id);

-- 6. FEEDBACK LOG (NEW)
-- Stores all user feedback for RLHF-like learning
CREATE TABLE IF NOT EXISTS feedback_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    message_id INTEGER NOT NULL,       -- References conversations.id
    
    -- Feedback details
    feedback_type TEXT NOT NULL,        -- 'thumbs_up', 'thumbs_down', 'rating', 'comment'
    feedback_value INTEGER,             -- 1-5 for rating, 1/-1 for thumbs
    feedback_text TEXT,                 -- Optional comment
    
    -- Context
    question_text TEXT,
    response_text TEXT,
    
    -- Temporal
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_message_feedback ON feedback_log(message_id);
CREATE INDEX IF NOT EXISTS idx_user_feedback ON feedback_log(user_id);

-- 7. MEMORY CONSOLIDATION LOG (NEW)
-- Tracks memory consolidation operations (like sleep consolidation in brain)
CREATE TABLE IF NOT EXISTS consolidation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    
    -- Consolidation details
    consolidation_type TEXT NOT NULL,   -- 'summary', 'cleanup', 'reorganization'
    messages_processed INTEGER,
    memories_created INTEGER,
    memories_deleted INTEGER,
    
    -- Performance metrics
    processing_time_seconds FLOAT,
    compression_achieved FLOAT,
    
    -- Temporal
    started_at DATETIME NOT NULL,
    completed_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_consolidation ON consolidation_log(user_id);

-- 8. CONVERSATION TOPICS (NEW)
-- Tracks conversation topics for better organization
CREATE TABLE IF NOT EXISTS conversation_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    
    -- Topic details
    topic_name TEXT NOT NULL,
    topic_keywords TEXT,                -- JSON array
    message_count INTEGER DEFAULT 0,
    
    -- Temporal
    first_mention DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_mention DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_topic ON conversation_topics(session_id);

-- ============================================================================
-- VIEWS FOR EASY ACCESS
-- ============================================================================

-- View: Recent conversations with importance scores
CREATE VIEW IF NOT EXISTS recent_important_conversations AS
SELECT 
    c.*,
    (c.importance_score * c.decay_factor * (1 + c.access_count * 0.1)) AS effective_importance
FROM conversations c
WHERE c.timestamp >= datetime('now', '-30 days')
ORDER BY effective_importance DESC;

-- View: User preference summary
CREATE VIEW IF NOT EXISTS user_preference_summary AS
SELECT 
    user_id,
    preference_category,
    COUNT(*) as preference_count,
    AVG(confidence) as avg_confidence
FROM user_preferences
GROUP BY user_id, preference_category;

-- View: Memory statistics per user
CREATE VIEW IF NOT EXISTS user_memory_stats AS
SELECT 
    c.user_id,
    COUNT(DISTINCT c.session_id) as session_count,
    COUNT(c.id) as total_messages,
    AVG(c.importance_score) as avg_importance,
    COUNT(DISTINCT e.id) as episodic_memories,
    COUNT(DISTINCT s.id) as semantic_memories
FROM conversations c
LEFT JOIN episodic_memory e ON e.user_id = c.user_id
LEFT JOIN semantic_memory s ON s.user_id = c.user_id
GROUP BY c.user_id;

-- ============================================================================
-- ADDITIONAL INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_conversations_importance_time 
ON conversations(importance_score DESC, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_semantic_memory_composite
ON semantic_memory(user_id, memory_type, confidence DESC);

CREATE INDEX IF NOT EXISTS idx_episodic_importance_time
ON episodic_memory(importance_score DESC, created_at DESC);
