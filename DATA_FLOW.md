# 🔄 FINBOT Data Flow & Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FINBOT System                            │
│                                                                  │
│  ┌────────────┐         ┌──────────────┐      ┌──────────────┐ │
│  │  Streamlit │ ───────▶│   Config     │◀─────│  .env File   │ │
│  │    UI      │         │  Settings    │      │  (API Keys)  │ │
│  └────────────┘         └──────────────┘      └──────────────┘ │
│        │                                                         │
│        │ (User uploads CSV/Excel)                               │
│        ▼                                                         │
│  ┌─────────────────────────────────────────┐                    │
│  │      src/core/data_processor.py         │                    │
│  │  ┌───────────────────────────────────┐  │                    │
│  │  │  • Load CSV/Excel                 │  │                    │
│  │  │  • Generate metadata              │  │                    │
│  │  │  • Create statistics              │  │                    │
│  │  │  • Build RAG document store       │  │                    │
│  │  └───────────────────────────────────┘  │                    │
│  └─────────────────────────────────────────┘                    │
│        │                        │                                │
│        │                        │                                │
│   (Analysis Mode)          (Chatbot Mode)                        │
│        │                        │                                │
│        ▼                        ▼                                │
│  ┌─────────────┐         ┌─────────────┐                        │
│  │  Analysis   │         │  Chatbot    │                        │
│  │   Agent     │         │   Agent     │                        │
│  └─────────────┘         └─────────────┘                        │
│        │                        │                                │
│        │                        └─────────────┐                 │
│        │                                      │                 │
│        ▼                                      ▼                 │
│  ┌─────────────────────┐         ┌──────────────────────┐      │
│  │   Groq LLM API      │         │  Conversation Memory │      │
│  │  (Llama 3.1 8B)     │         │   src/memory/        │      │
│  │                     │         │  conversation.py     │      │
│  │  • Health Score     │         │                      │      │
│  │  • Risk Assessment  │         │  • Message history   │      │
│  │  • Insights         │         │  • Context window    │      │
│  │  • Recommendations  │         │  • Persistence       │      │
│  └─────────────────────┘         └──────────────────────┘      │
│        │                                      │                 │
│        │                                      │                 │
│        └──────────────┬───────────────────────┘                 │
│                       │                                         │
│                       ▼                                         │
│              ┌─────────────────┐                                │
│              │  Display Results│                                │
│              │   in Streamlit  │                                │
│              └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## Analysis Mode Flow

```
User uploads CSV
       │
       ▼
┌──────────────────┐
│ DataProcessor    │
│ • Load file      │
│ • Validate       │
│ • Extract stats  │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Create Summary   │
│ • Metadata       │
│ • Statistics     │
│ • Sample data    │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Analysis Agent   │
│ • Build prompt   │
│ • Call Groq LLM  │
│ • Parse response │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Display Results  │
│ • Health Score   │
│ • Risk Level     │
│ • Insights       │
│ • Recommendations│
└──────────────────┘
```

## Chatbot Mode Flow

```
User asks question
       │
       ▼
┌──────────────────┐
│ Chatbot Agent    │
│ • Receive query  │
└──────────────────┘
       │
       ├────────────────┐
       ▼                ▼
┌──────────────┐  ┌─────────────┐
│ Get Chat     │  │ Search RAG  │
│ History      │  │ Documents   │
│ (memory)     │  │ (data store)│
└──────────────┘  └─────────────┘
       │                │
       └────────┬───────┘
                ▼
      ┌───────────────────┐
      │ Build Context     │
      │ • Recent messages │
      │ • Relevant docs   │
      │ • Data summary    │
      └───────────────────┘
                │
                ▼
      ┌───────────────────┐
      │ Call Groq LLM     │
      │ • Generate answer │
      └───────────────────┘
                │
                ▼
      ┌───────────────────┐
      │ Save to Memory    │
      │ • User message    │
      │ • Bot response    │
      └───────────────────┘
                │
                ▼
      ┌───────────────────┐
      │ Display Answer    │
      │ in chat interface │
      └───────────────────┘
```

## Memory System Architecture

```
┌────────────────────────────────────────┐
│        Conversation Memory             │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │     Message Storage              │ │
│  │  ┌────────────────────────────┐  │ │
│  │  │  Message 1: User           │  │ │
│  │  │  Message 2: Assistant      │  │ │
│  │  │  Message 3: User           │  │ │
│  │  │  Message 4: Assistant      │  │ │
│  │  │  ...                       │  │ │
│  │  └────────────────────────────┘  │ │
│  └──────────────────────────────────┘ │
│               │                        │
│               ├─────────────┐          │
│               ▼             ▼          │
│    ┌──────────────┐  ┌──────────────┐ │
│    │ Recent       │  │ Persistence  │ │
│    │ Window       │  │ (JSON files) │ │
│    │ (last N msgs)│  │              │ │
│    └──────────────┘  └──────────────┘ │
└────────────────────────────────────────┘
              │
              ▼ (provides context to)
    ┌─────────────────┐
    │  Chatbot Agent  │
    └─────────────────┘
```

## RAG (Retrieval Augmented Generation) Flow

```
CSV Upload
    │
    ▼
┌─────────────────┐
│ DataProcessor   │
│ • Parse CSV     │
│ • Extract info  │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Create Documents│
│ • Dataset       │
│   summary       │
│ • Column info   │
│ • Statistics    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ DocumentStore   │
│ (in-memory)     │
│ • Store docs    │
│ • Index content │
└─────────────────┘
    │
    ▼
    (User asks question)
    │
    ▼
┌─────────────────┐
│ Keyword Search  │
│ • Match query   │
│ • Rank results  │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Return Top-K    │
│ relevant docs   │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Add to LLM      │
│ context         │
└─────────────────┘
```

## File Processing Pipeline

```
File Upload
    │
    ▼
┌─────────────────┐
│ Validation      │
│ • Type check    │
│ • Size check    │
│ • Format check  │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Load Data       │
│ • CSV: pandas   │
│ • Excel: pandas │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Clean Data      │
│ • Remove empty  │
│ • Strip spaces  │
│ • Parse dates   │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Generate        │
│ Metadata        │
│ • Columns       │
│ • Types         │
│ • Stats         │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Create Summary  │
│ • Text format   │
│ • For LLM       │
└─────────────────┘
```

## LLM Interaction Pattern

```
User Input
    │
    ▼
┌─────────────────┐
│ Build Prompt    │
│ • System msg    │
│ • Context       │
│ • User query    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Call Groq API   │
│ POST /messages  │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Receive         │
│ Response        │
│ (JSON)          │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Parse Response  │
│ • Extract text  │
│ • Clean format  │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Display to User │
└─────────────────┘
```

## Configuration Flow

```
.env file
    │
    ▼
┌─────────────────┐
│ load_dotenv()   │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ config/         │
│ settings.py     │
│ • GROQ_API_KEY  │
│ • MODEL         │
│ • TEMPERATURE   │
│ • Paths         │
└─────────────────┘
    │
    ├───────────┬────────────┬──────────┐
    ▼           ▼            ▼          ▼
┌─────────┐ ┌────────┐ ┌─────────┐ ┌──────┐
│ Agents  │ │ Memory │ │  Core   │ │  UI  │
└─────────┘ └────────┘ └─────────┘ └──────┘
```

## Directory Structure & Responsibilities

```
finbot-clean/
│
├── app.py ──────────────────── Main UI + Routing
│
├── config/
│   └── settings.py ────────── Global Configuration
│
├── src/
│   ├── core/
│   │   └── data_processor.py ─ File I/O + RAG
│   │
│   ├── agents/
│   │   ├── analysis_agent.py ─ Financial Analysis
│   │   └── chatbot_agent.py ── Q&A Chatbot
│   │
│   ├── memory/
│   │   └── conversation.py ─── Chat History
│   │
│   └── utils/
│       └── helpers.py ─────── Utility Functions
│
└── data/
    ├── uploads/ ───────────── User CSV/Excel
    ├── memory/ ────────────── Chat Sessions
    └── vector_store/ ──────── RAG Documents
```

## Error Handling Flow

```
User Action
    │
    ▼
┌─────────────────┐
│ Try Operation   │
└─────────────────┘
    │
    ├─ Success ──────────▶ Continue
    │
    └─ Exception
         │
         ▼
    ┌─────────────────┐
    │ Catch Exception │
    │ • Log error     │
    │ • Create msg    │
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ Display Error   │
    │ to User         │
    │ (Streamlit)     │
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ Graceful        │
    │ Degradation     │
    │ • Show fallback │
    │ • Suggest fix   │
    └─────────────────┘
```

## Key Design Patterns Used

1. **Singleton Pattern**: Global instances (memory manager, document store)
2. **Factory Pattern**: Creating agents and memory instances
3. **Strategy Pattern**: Different modes (Analysis vs Chatbot)
4. **Repository Pattern**: Data access through DataProcessor
5. **Chain of Responsibility**: Error handling cascade

## Performance Considerations

- **Lazy Loading**: Data loaded only when needed
- **Caching**: Streamlit session state for expensive operations
- **Streaming**: Could be added for long responses
- **Batch Processing**: File validation before processing
- **Memory Management**: Sliding window, not full history

---

This architecture ensures:
- ✅ Clean separation of concerns
- ✅ Easy to test and maintain
- ✅ Scalable for future features
- ✅ Efficient resource usage
- ✅ Good error recovery
