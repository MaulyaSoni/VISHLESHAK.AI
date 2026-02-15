# 🏗️ FINBOT v4 - Phase 1 Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FINBOT v4 - Enhanced Memory System                     │
│                              Phase 1 Architecture                             │
└─────────────────────────────────────────────────────────────────────────────┘

                                    ┌───────────────┐
                                    │  User Query   │
                                    └───────┬───────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────┐
                    │   EnhancedMemoryManager (Orchestrator)    │
                    │   • Strategy Selection                     │
                    │   • Context Assembly                       │
                    │   • Consolidation Control                  │
                    └───────────────────────────────────────────┘
                                            │
                ┌───────────────────────────┼───────────────────────────┐
                │                           │                           │
                ▼                           ▼                           ▼
    ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
    │  ADD Operations  │      │ RETRIEVE Context │      │  CONSOLIDATION   │
    └──────────────────┘      └──────────────────┘      └──────────────────┘
                │                           │                           │
                │                           │                           │
                ▼                           ▼                           ▼


════════════════════════════════════════════════════════════════════════════
                             MEMORY TIER ARCHITECTURE
════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: SHORT-TERM MEMORY (Immediate Context)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  ConversationBufferWindowMemory (LangChain)          │                   │
│  │  • Last 10 messages                                  │                   │
│  │  • In-memory buffer                                  │                   │
│  │  • Immediate recall                                  │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                                                                               │
│  Characteristics:                                                             │
│  ✓ Fast access (< 1ms)                                                       │
│  ✓ Always retrieved                                                          │
│  ✓ Recent conversation context                                               │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 2: WORKING MEMORY (Summarized Context)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  Conversation Summaries                              │                   │
│  │  • Updated every 10 messages                         │                   │
│  │  • LLM-generated summary                             │                   │
│  │  • Compression ratio: 30%                            │                   │
│  └──────────────────────────────────────────────────────┘                   │
│           │                                                                   │
│           ▼                                                                   │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  working_memory table (SQLite)                       │                   │
│  │  • session_id, summary_text                          │                   │
│  │  • window_start, window_end                          │                   │
│  │  • compression_ratio                                 │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                                                                               │
│  Characteristics:                                                             │
│  ✓ Compressed context (500 words max)                                        │
│  ✓ Covers 50 message window                                                  │
│  ✓ Reduces prompt token usage                                                │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 3: LONG-TERM MEMORY (Semantic Search)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  Vector Database (ChromaDB)                          │                   │
│  │  • Embedding-based similarity search                 │                   │
│  │  • All conversation turns stored                     │                   │
│  │  • Metadata filtering                                │                   │
│  └──────────────────────────────────────────────────────┘                   │
│           │                                                                   │
│           ▼                                                                   │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  conversations table (SQLite)                        │                   │
│  │  • id, session_id, user_id                           │                   │
│  │  • message_type, message, timestamp                  │                   │
│  │  • importance_score, decay_factor                    │                   │
│  │  • access_count, last_accessed                       │                   │
│  │  • topic, sentiment, metadata                        │                   │
│  └──────────────────────────────────────────────────────┘                   │
│           │                                                                   │
│           ▼                                                                   │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  Importance-Weighted Retrieval                       │                   │
│  │  • Retrieval Score = f(importance, similarity,       │                   │
│  │                        recency, access_count)        │                   │
│  │  • Top K results (default: 5)                        │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                                                                               │
│  Characteristics:                                                             │
│  ✓ Semantic similarity search                                                │
│  ✓ Importance-weighted ranking                                               │
│  ✓ Retrieved when keywords detected                                          │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 4: SEMANTIC MEMORY (Facts & Preferences)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  Extracted Knowledge                                 │                   │
│  │  • Facts learned from conversations                  │                   │
│  │  • User preferences                                  │                   │
│  │  • Insights and rules                                │                   │
│  └──────────────────────────────────────────────────────┘                   │
│           │                                                                   │
│           ▼                                                                   │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  semantic_memory table (SQLite)                      │                   │
│  │  • user_id, memory_type                              │                   │
│  │  • key, value                                        │                   │
│  │  • confidence, evidence_count                        │                   │
│  │  • first_learned, last_updated                       │                   │
│  │  • access_count, relevance_score                     │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                                                                               │
│  Memory Types:                                                                │
│  • 'fact' - Factual information                                              │
│  • 'preference' - User preferences                                           │
│  • 'insight' - Discovered insights                                           │
│  • 'rule' - Learned rules                                                    │
│                                                                               │
│  Characteristics:                                                             │
│  ✓ Confidence-scored (0-1)                                                   │
│  ✓ Evidence-based reinforcement                                              │
│  ✓ Always retrieved (up to K items)                                          │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 5: EPISODIC MEMORY (Important Moments)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  High-Importance Sequences                           │                   │
│  │  • Breakthrough moments                              │                   │
│  │  • Critical decisions                                │                   │
│  │  • Important insights                                │                   │
│  └──────────────────────────────────────────────────────┘                   │
│           │                                                                   │
│           ▼                                                                   │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │  episodic_memory table (SQLite)                      │                   │
│  │  • session_id, user_id                               │                   │
│  │  • episode_summary, full_context                     │                   │
│  │  • importance_score, episode_type                    │                   │
│  │  • tags, message_ids                                 │                   │
│  │  • emotional_valence                                 │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                                                                               │
│  Episode Types:                                                               │
│  • 'insight' - New understanding                                             │
│  • 'decision' - Important decision made                                      │
│  • 'preference' - Strong preference stated                                   │
│  • 'breakthrough' - Major discovery                                          │
│                                                                               │
│  Characteristics:                                                             │
│  ✓ Never forgotten (preserved)                                               │
│  ✓ Importance threshold: 0.8+                                                │
│  ✓ Retrieved when keywords detected                                          │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘


════════════════════════════════════════════════════════════════════════════
                           IMPORTANCE SCORING SYSTEM
════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                         LSTM-Inspired Gating Mechanism                        │
└─────────────────────────────────────────────────────────────────────────────┘

                            ┌──────────────────┐
                            │  Input Message   │
                            └────────┬─────────┘
                                     │
                                     ▼
                ┌────────────────────────────────────────┐
                │      IMPORTANCE SCORER                 │
                │   (Multi-Factor Calculation)           │
                └────────────────────────────────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
┌────────────────┐          ┌────────────────┐          ┌────────────────┐
│ Message Length │          │    Keywords    │          │ Question Depth │
│   Weight: 0.15 │          │  Weight: 0.25  │          │  Weight: 0.20  │
└────────────────┘          └────────────────┘          └────────────────┘
        │                            │                            │
        │         ┌──────────────────┴────────────────┐          │
        │         │                                    │          │
        ▼         ▼                                    ▼          ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        User Feedback                                    │
│                        Weight: 0.25                                     │
└────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │ FINAL IMPORTANCE SCORE │
                        │      (0.0 - 1.0)       │
                        └────────────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │   STORED IN DATABASE   │
                        └────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         DECAY MECHANISM (Forget Gate)                         │
└─────────────────────────────────────────────────────────────────────────────┘

    Original Importance ──┐
                          │
    Time (days) ─────────►│  DECAY CALCULATOR
                          │  • decay_factor = 0.99^days
    Access Count ────────►│  • access_boost = count × 0.1
                          │
                          └──► Effective Importance
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │  Forgetting Decision │
                          │                      │
                          │  if < threshold:     │
                          │    DELETE            │
                          │  else:               │
                          │    KEEP              │
                          └──────────────────────┘


════════════════════════════════════════════════════════════════════════════
                           CONSOLIDATION PROCESS
════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTOMATIC CONSOLIDATION (Like Sleep)                       │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────┐
    │  TRIGGERS:                                          │
    │  • Every 24 hours                                   │
    │  • After 100 messages                               │
    └─────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────┐
    │  STEP 1: Update Working Memory                      │
    │  • Summarize recent 50 messages                     │
    │  • Compress to ~500 words                           │
    │  • Save to working_memory table                     │
    └─────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────┐
    │  STEP 2: Extract Semantic Knowledge                 │
    │  • Identify preferences                             │
    │  • Extract facts                                    │
    │  • Capture insights                                 │
    │  • Save to semantic_memory table                    │
    └─────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────┐
    │  STEP 3: Identify Episodes                          │
    │  • Find high-importance sequences                   │
    │  • Create episode summaries                         │
    │  • Tag by type (insight/decision/etc)               │
    │  • Save to episodic_memory table                    │
    └─────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────┐
    │  STEP 4: Apply Decay                                │
    │  • Update decay_factor for all messages             │
    │  • Recalculate effective importance                 │
    └─────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────┐
    │  STEP 5: Selective Forgetting                       │
    │  • Delete messages < threshold                      │
    │  • Preserve episodic memories                       │
    │  • Keep recent messages (< 30 days)                 │
    └─────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────┐
    │  RESULT: Optimized Memory                           │
    │  • Reduced storage                                  │
    │  • Preserved important information                  │
    │  • Faster retrieval                                 │
    └─────────────────────────────────────────────────────┘


════════════════════════════════════════════════════════════════════════════
                         CONTEXT RETRIEVAL FLOW
════════════════════════════════════════════════════════════════════════════

                        ┌───────────────┐
                        │  User Query   │
                        └───────┬───────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Strategy Selection   │
                    │  • Conservative       │
                    │  • Hybrid (default)   │
                    │  • Aggressive         │
                    └───────────┬───────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
    ┌──────────────────┐           ┌──────────────────┐
    │ TIER 1: Short    │           │ TIER 2: Working  │
    │ Last 10 msgs     │◄──────────┤ Summary (500w)   │
    │ (Always)         │           │ (Always)         │
    └──────────────────┘           └──────────────────┘
                │
                ▼
    ┌──────────────────────────────────────────────┐
    │  Keyword Detection                           │
    │  • Historical keywords? → TIER 3            │
    │  • Episodic keywords? → TIER 5              │
    └──────────────────────────────────────────────┘
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
┌────────────┐   ┌────────────┐   ┌────────────┐
│ TIER 3:    │   │ TIER 4:    │   │ TIER 5:    │
│ Long-term  │   │ Semantic   │   │ Episodic   │
│ Top 5-10   │   │ Top 3-5    │   │ Top 2-5    │
│ (Conditio  │   │ (Always)   │   │ (Conditio  │
│ nal)       │   │            │   │ nal)       │
└────────────┘   └────────────┘   └────────────┘
        │               │               │
        └───────┬───────┴───────┬───────┘
                │               │
                ▼               ▼
        ┌─────────────────────────────┐
        │  Context Assembly            │
        │  • Deduplicate              │
        │  • Order by relevance       │
        │  • Format for prompt        │
        └─────────────────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │ Formatted     │
                │ Context for   │
                │ LLM Prompt    │
                └───────────────┘


════════════════════════════════════════════════════════════════════════════
                              DATA FLOW
════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                           WRITE PATH (add_turn)                               │
└─────────────────────────────────────────────────────────────────────────────┘

User Message + Bot Response
         │
         ▼
    Calculate Importance ────┬──────► TIER 1: Add to buffer
         │                   │
         │                   ├──────► TIER 2: Append to working memory
         │                   │
         │                   ├──────► TIER 3: Save to DB + Vector Store
         │                   │
         │                   │        (Later, during consolidation)
         │                   ├──────► TIER 4: Extract semantic knowledge
         │                   │
         │                   └──────► TIER 5: Identify episodes
         │
         ▼
    Check if consolidation needed
         │
         ├─► Yes → Run consolidation
         │
         └─► No → Continue


┌─────────────────────────────────────────────────────────────────────────────┐
│                         READ PATH (retrieve_context)                          │
└─────────────────────────────────────────────────────────────────────────────┘

Query + Strategy
         │
         ▼
    Analyze Query
         │
         ├──────► TIER 1: Get last N messages (always)
         │
         ├──────► TIER 2: Get summary if exists (always)
         │
         ├──────► TIER 3: Vector search (if historical keywords)
         │                 └─► Rank by retrieval_score
         │
         ├──────► TIER 4: Get semantic memories (always)
         │
         └──────► TIER 5: Get episodes (if episodic keywords)
         │
         ▼
    Assemble Context
         │
         ▼
    Format for Prompt
         │
         ▼
    Return to LLM


════════════════════════════════════════════════════════════════════════════
                           COMPONENT INTERACTIONS
════════════════════════════════════════════════════════════════════════════

┌────────────────────┐
│ EnhancedMemory     │◄──────┐
│ Manager            │       │
└─────────┬──────────┘       │
          │                  │
          ├──────────────────┼──────────┐
          │                  │          │
          ▼                  ▼          ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Importance   │   │ Memory       │   │ Memory       │
│ Scorer       │   │ Consolidator │   │ Database     │
└──────────────┘   └──────────────┘   └──────────────┘
                           │                  │
                           │                  │
                           ▼                  ▼
                   ┌──────────────┐   ┌──────────────┐
                   │ LLM (Groq)   │   │ SQLite DB    │
                   └──────────────┘   └──────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │ Vector Store │
                   │ (ChromaDB)   │
                   └──────────────┘


════════════════════════════════════════════════════════════════════════════
                                SUMMARY
════════════════════════════════════════════════════════════════════════════

✅ 5 Memory Tiers
✅ LSTM-Inspired Gating (Input/Forget/Output)
✅ Importance-Weighted Storage & Retrieval  
✅ Automatic Consolidation (Every 24h or 100 msgs)
✅ Selective Forgetting (Decay + Threshold)
✅ Strategy-Based Retrieval (Conservative/Hybrid/Aggressive)
✅ Multi-Factor Importance Scoring
✅ Access-Based Reinforcement
✅ Semantic Knowledge Extraction
✅ Episodic Memory Preservation

════════════════════════════════════════════════════════════════════════════
```

---

**Architecture Complete! 🎉**

This multi-tiered, LSTM-inspired memory system provides:
- **Scalability** - Handles unlimited conversation length
- **Intelligence** - Retrieves what's truly relevant
- **Efficiency** - Automatic summarization and cleanup
- **Adaptability** - Learns from user interactions
- **Performance** - Optimized queries and caching

Ready for integration! 🚀
