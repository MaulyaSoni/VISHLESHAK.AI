# Vishleshak AI — Enterprise Data Analysis Platform

**Vishleshak** (विश्लेषक) — *The Analyser*

An intelligent, production-grade data analysis platform powered by Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and agentic reasoning. Vishleshak AI enables organizations to upload datasets and interact with them through natural language, combining statistical analysis, visualization, conversational AI, and multi-agent reasoning in a secure, user-authenticated environment.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Security and Privacy](#security-and-privacy)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Vishleshak AI is a comprehensive data analytics assistant designed for enterprises and data teams. It provides three primary interaction modes:

1. **Comprehensive Analysis Mode** — Automated statistical profiling and visualization
2. **RAG Chatbot Mode** — Natural language queries grounded in uploaded data
3. **Agentic ReAct Engine** — Multi-step reasoning for complex analytical questions

The platform includes enterprise-grade features such as role-based authentication, per-user data isolation, persistent conversation history, and vector search capabilities.

---

## Features

### Analysis and Insights

- **Automated Data Profiling** — Summary statistics, data types, missing value detection, completeness scoring
- **Statistical Analysis** — Descriptive statistics (mean, median, std deviation, skewness, kurtosis) for numeric columns
- **Pattern Detection** — Trend identification, seasonality detection, anomaly flagging
- **AI-Powered Insights** — LLM-generated narrative summaries of key analytical findings
- **Rich Visualizations** — Auto-generated charts and plots (distributions, correlations, time-series, box plots, heatmaps, scatter matrices)
- **Interactive Dashboards** — Plotly-based interactive charts with zoom, pan, and export capabilities

### Conversational Intelligence

- **Natural Language Interface** — Ask analytical questions about datasets in plain English
- **Retrieval-Augmented Generation** — Answers grounded in actual data, minimizing hallucination
- **Semantic Vector Search** — Advanced retrieval over document embeddings
- **Conversation Memory** — Multi-turn chat with persistent context
- **Quick-Start Prompts** — Pre-defined analytical templates for rapid querying
- **Chat History** — Persistent, searchable conversation logs organized by date

### Agentic Reasoning

- **Multi-Step Reasoning** — ReAct (Reason + Act) agent framework for complex analytical questions
- **Intelligent Tool Selection** — Automatic routing to statistical tools, visualization engines, and knowledge bases
- **Self-Reflection** — Built-in response improvement and critique loop
- **Transparent Reasoning Trace** — Step-by-step thought process visibility (admin/debug mode)

### User Management and Security

- **Secure Authentication** — Registration and login with bcrypt password hashing
- **Session Management** — Token-based session management with automatic expiration
- **Per-User Isolation** — Complete data and conversation separation between users
- **Profile Management** — User-editable profile information
- **Password Security** — Self-service password change with verification
- **Account Management** — User account deletion with confirmation

### Data Management

- **Multi-Format Support** — CSV, XLSX, XLS file uploads
- **Data Preview** — Head/tail view with column information and type detection
- **In-Session Dataset Switching** — Replace datasets without re-authentication
- **Vector Indexing** — Automatic embedding generation for semantic search
- **Embedding Cache** — Optimized re-computation of embeddings for unchanged data

### Session and History Management

- **Persistent Chat History** — SQLite-backed conversation storage
- **Temporal Organization** — Conversations grouped by date (Today, Yesterday, Last 7 Days, Older)
- **Full-Text Search** — Search conversations by content
- **Session Management** — Create new chats while retaining historical sessions
- **Data Export** — Export conversation history as JSON

### User Settings

- **Profile Tab** — Username, email, registration date, name editing
- **Security Tab** — Password management, account deletion
- **Preferences Tab** — Feature visibility and reasoning process toggles
- **Data Management Tab** — Conversation export and data retrieval

---

## System Architecture

```
vishleshak-ai/
├── app.py                        # Main Streamlit entry point
│
├── agentic_core/                 # ReAct agent engine
│   ├── react_agent.py            # Multi-step reasoning loop
│   ├── reflection_layer.py       # Self-critique & improvement
│   ├── tool_selector.py          # Automatic tool routing
│   ├── agent_memory.py           # Agent working memory
│   └── prompts/                  # System, ReAct & reflection prompts
│
├── analyzers/                    # Analysis pipeline
│   ├── statistical_analyzer.py   # Descriptive stats engine
│   ├── pattern_detector.py       # Trend & anomaly detection
│   └── insight_generator.py      # LLM narrative generation
│
├── auth/                         # Authentication layer
│   ├── auth_manager.py           # Login / register / token logic
│   ├── password_utils.py         # Bcrypt hashing utilities
│   └── session_manager.py        # Session token lifecycle
│
├── chatbot/                      # Q&A chatbot pipeline
│   ├── qa_chain.py               # Main LangChain QA chain
│   ├── context_manager.py        # Conversation context window
│   ├── cot_reasoner.py           # Chain-of-thought reasoning
│   ├── question_decomposer.py    # Multi-part question splitting
│   ├── response_formatter.py     # Output formatting
│   ├── sequential_chain.py       # Multi-step chain orchestration
│   ├── quality_scorer.py         # Internal response scoring
│   ├── feedback_collector.py     # Thumbs up/down feedback
│   ├── improvement_loop.py       # Quality-driven refinement
│   ├── preference_learner.py     # User preference adaptation
│   └── prompt_templates.py       # Prompt library
│
├── config/                       # Centralised configuration
│   ├── settings.py               # Global app settings
│   ├── agent_config.py           # Agent parameters
│   ├── chain_config.py           # LangChain config
│   ├── memory_config.py          # Memory settings
│   ├── rag_config.py             # RAG parameters
│   └── tool_config.py            # Tool registry config
│
├── core/                         # Core AI infrastructure
│   ├── llm.py                    # LLM client (Groq)
│   ├── embeddings.py             # Embedding model wrapper
│   ├── memory.py                 # Base memory manager
│   ├── enhanced_memory.py        # Long-term + semantic memory
│   ├── memory_consolidation.py   # Memory compression
│   ├── memory_database.py        # Memory persistence layer
│   └── importance_scorer.py      # Memory importance ranking
│
├── database/                     # Relational database layer
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── db_manager.py             # DB session & connection pool
│   ├── migrations.py             # Schema migration utilities
│   ├── user_repository.py        # User CRUD operations
│   └── chat_repository.py        # Conversation CRUD operations
│
├── rag/                          # RAG pipeline
│   ├── document_loader.py        # CSV/Excel → LangChain docs
│   ├── vector_store.py           # FAISS / Chroma vector store
│   ├── retriever.py              # Semantic retrieval logic
│   ├── embeddings_cache.py       # Embedding memoisation
│   ├── knowledge_base.py         # Static domain knowledge
│   └── advanced/                 # Advanced RAG strategies
│
├── tools/                        # Agent tool registry
│   ├── tool_registry.py          # Tool registration & lookup
│   ├── custom_tools/             # Domain-specific tools
│   ├── langchain_tools/          # LangChain tool wrappers
│   └── specialized/              # Chart, stats, search tools
│
├── ui/                           # Streamlit UI components
│   ├── auth_ui.py                # Login / Register page
│   ├── chat_history_ui.py        # Sidebar conversation history
│   ├── user_settings_ui.py       # Settings panel (4 tabs)
│   └── claude_loaders.py         # Animated loading screens
│
├── utils/                        # Shared utilities
│   ├── data_loader.py            # File parsing & validation
│   ├── dashboard_visualizer.py   # Chart generation (Plotly)
│   └── helpers.py                # General helper functions
│
├── styles/
│   └── claude_theme.py           # Dark theme token system
│
├── knowledge_base/               # Static RAG documents
│   ├── finance/
│   ├── education/
│   └── general/
│
└── data/
    ├── uploads/                  # User-uploaded datasets
    ├── memory/                   # Conversation JSON store
    └── vector_store/             # Persisted FAISS indexes
## System Architecture

### Directory Structure

```
vishleshak-ai/
├── app.py                          # Main Streamlit application entry point
├── requirements.txt                # Python dependency specifications
├── .env                            # Environment configuration (local)
│
├── agentic_core/                   # ReAct Agent Framework
│   ├── react_agent.py              # Multi-step reasoning loop implementation
│   ├── reflection_layer.py         # Self-critique and response improvement
│   ├── tool_selector.py            # Intelligent tool routing and selection
│   ├── agent_memory.py             # Agent working memory management
│   └── prompts/
│       ├── react_prompt.py         # ReAct reasoning prompts
│       ├── reflection_prompt.py    # Self-improvement prompts
│       └── system_prompt.py        # System-level instructions
│
├── analyzers/                      # Statistical Analysis Pipeline
│   ├── statistical_analyzer.py     # Descriptive statistics engine
│   ├── pattern_detector.py         # Trend and anomaly detection
│   └── insight_generator.py        # LLM-powered narrative generation
│
├── auth/                           # Authentication and Authorization
│   ├── auth_manager.py             # Login, registration, token logic
│   ├── password_utils.py           # Bcrypt hashing utilities
│   └── session_manager.py          # Session token lifecycle management
│
├── chatbot/                        # Conversational AI Pipeline
│   ├── qa_chain.py                 # LangChain QA chain orchestration
│   ├── context_manager.py          # Conversation context window management
│   ├── cot_reasoner.py             # Chain-of-thought reasoning
│   ├── question_decomposer.py      # Multi-part question decomposition
│   ├── response_formatter.py       # Output formatting and refinement
│   ├── sequential_chain.py         # Multi-step chain orchestration
│   ├── quality_scorer.py           # Response quality assessment
│   ├── feedback_collector.py       # User feedback capture
│   ├── improvement_loop.py         # Iterative quality refinement
│   ├── preference_learner.py       # User preference adaptation
│   └── prompt_templates.py         # Prompt library and management
│
├── config/                         # Centralized Configuration
│   ├── settings.py                 # Global application settings
│   ├── agent_config.py             # Agent parameter configuration
│   ├── chain_config.py             # LangChain configuration
│   ├── memory_config.py            # Memory system configuration
│   ├── rag_config.py               # RAG pipeline configuration
│   └── tool_config.py              # Tool registry configuration
│
├── core/                           # Core AI Infrastructure
│   ├── llm.py                      # LLM client (Groq API wrapper)
│   ├── embeddings.py               # Embedding model wrapper
│   ├── memory.py                   # Base memory management
│   ├── enhanced_memory.py          # Long-term and semantic memory
│   ├── memory_consolidation.py     # Memory compression utilities
│   ├── memory_database.py          # Memory persistence layer
│   └── importance_scorer.py        # Memory importance ranking
│
├── database/                       # Relational Database Layer
│   ├── models.py                   # SQLAlchemy ORM models
│   ├── db_manager.py               # Database session and connection pool
│   ├── migrations.py               # Schema migration utilities
│   ├── user_repository.py          # User CRUD operations
│   └── chat_repository.py          # Conversation CRUD operations
│
├── rag/                            # RAG (Retrieval-Augmented Generation)
│   ├── document_loader.py          # CSV/Excel document loading
│   ├── vector_store.py             # FAISS/Chroma vector store wrapper
│   ├── retriever.py                # Semantic retrieval implementation
│   ├── embeddings_cache.py         # Embedding cache layer
│   ├── knowledge_base.py           # Static knowledge base management
│   └── advanced/                   # Advanced RAG strategies
│
├── tools/                          # Agent Tool Registry
│   ├── tool_registry.py            # Tool registration and lookup
│   ├── custom_tools/               # Domain-specific tools
│   ├── langchain_tools/            # LangChain tool wrappers
│   └── specialized/                # Specialized tools (charts, stats, search)
│
├── ui/                             # Streamlit UI Components
│   ├── auth_ui.py                  # Login and registration interface
│   ├── chat_history_ui.py          # Sidebar conversation history
│   ├── user_settings_ui.py         # Settings panel UI (4 tabs)
│   ├── loader_animations.py        # Loading animation components
│   └── claude_loaders.py           # Custom loader implementations
│
├── utils/                          # Shared Utilities
│   ├── data_loader.py              # File parsing and validation
│   ├── dashboard_visualizer.py     # Chart generation (Plotly)
│   └── helpers.py                  # General utility functions
│
├── styles/                         # UI Styling
│   └── claude_theme.py             # Dark theme token system
│
├── knowledge_base/                 # Static RAG Documents
│   ├── finance/
│   ├── education/
│   └── general/
│
├── data/                           # Data Storage
│   ├── uploads/                    # User-uploaded datasets
│   ├── memory/                     # Conversation JSON store
│   └── vector_store/               # Persisted vector indexes
│
└── database/                       # SQLite Database
    └── vishleshak.db               # Application database
```

### Data Flow

1. **User Upload** → Data Loader → Vector Indexing → Vector Store
2. **User Query** → RAG Retriever → LLM Chain → Response Formatter
3. **Complex Query** → ReAct Agent → Tool Selection → Reflection Layer
4. **Conversation** → Context Manager → Memory → SQLite

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Frontend** | Streamlit | ≥1.42.0 |
| **Runtime** | Python | 3.9+ |
| **LLM Provider** | Groq API | Latest |
| **LLM Models** | Llama 3.1, Mixtral 8x7B | Latest |
| **Embeddings** | Sentence Transformers | ≥2.5.1 |
| **Orchestration** | LangChain | 0.1.16 |
| **Agent Framework** | LangGraph | ≥0.0.20 |
| **Vector Database** | Chroma DB | ≥0.5.0 |
| **Relational Database** | SQLite | 3.x |
| **ORM** | SQLAlchemy | (via LangChain) |
| **Data Processing** | Pandas, NumPy | ≥2.2.0, ≥1.24.0 |
| **Statistics** | SciPy, Scikit-learn, Statsmodels | ≥1.11.0, ≥1.4.0 |
| **Time Series** | Prophet | ≥1.1.5 |
| **Visualization** | Plotly, Matplotlib, Seaborn | 5.20.0, 3.8.3, 0.13.2 |
| **File Handling** | OpenPyXL, xlrd | ≥3.1.2, ≥2.0.1 |
| **Security** | Bcrypt | (via werkzeug) |
| **Document Processing** | PyPDF, python-docx, Markdown | 4.0.1, 1.1.0, 3.5.2 |

---

## Installation

### Prerequisites

- Python 3.9 or higher
- Git
- Groq API key (free tier available at [console.groq.com](https://console.groq.com))
- Minimum 2GB RAM
- 500MB free disk space

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd vishleshak-ai
```

#### 2. Create Python Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration (see Configuration section below)
```

#### 5. Initialize Database

```bash
python -c "from database.db_manager import init_db; init_db()"
```

#### 6. Launch Application

```bash
streamlit run app.py
```

The application will be accessible at `http://localhost:8501`

---

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# LLM Provider
GROQ_API_KEY=your_groq_api_key_here

# LangSmith Observability (Optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=Vishleshak_AI

# Database
DATABASE_URL=sqlite:///./vishleshak.db

# Session Configuration
SESSION_TIMEOUT_MINUTES=60
MAX_UPLOAD_SIZE_MB=100

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
RETRIEVAL_K=5

# Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
TEMPERATURE=0.7
MAX_TOKENS=2048
```

### Key Configuration Files

- **config/settings.py** — Application-wide settings
- **config/agent_config.py** — Agent behavior parameters
- **config/rag_config.py** — RAG pipeline tuning
- **config/memory_config.py** — Memory system parameters

---

## Usage Guide

### 1. User Registration and Authentication

1. Navigate to the application
2. Click "Register" to create a new account
3. Provide:
   - Full Name
   - Username (unique)
   - Email Address
   - Password (minimum 8 characters, mixed case, digit, and special character)
4. Click "Sign Up"
5. Login with your username and password

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*)

### 2. Dataset Upload

1. In the sidebar, click "Upload Dataset"
2. Select a file (.csv, .xlsx, or .xls)
3. Review the preview:
   - First and last rows
   - Column names and data types
   - Missing value count
4. Click "Confirm Upload"
5. The system automatically generates embeddings and builds the vector index

### 3. Comprehensive Analysis Mode

1. From the sidebar, select "Comprehensive Analysis"
2. Click "Run Analysis"
3. The system will:
   - Generate descriptive statistics
   - Detect patterns and anomalies
   - Generate relevant visualizations (20+ charts)
   - Produce AI-powered narrative insights
4. Export visualizations using the export icon on each chart
5. Download analysis report as JSON or CSV

### 4. RAG Chatbot Mode

1. From the sidebar, select "RAG Chatbot"
2. Ask analytical questions about your dataset in natural language:
   - "What are the top 5 cities by total sales?"
   - "Are there significant outliers in the revenue column?"
   - "What is the correlation between price and quantity?"
3. The system will:
   - Retrieve relevant data
   - Generate contextual responses
   - Maintain conversation history
4. Use quick-start prompts for common queries
5. View past conversations in the sidebar (grouped by date)

### 5. Agentic Reasoning (Advanced)

1. From the sidebar, select "Agentic ReAct"
2. Ask complex, multi-step questions:
   - "Analyze the sales trend and predict the next quarter"
   - "Compare revenue patterns across regions and identify top performers"
3. The agent will:
   - Break down the question into sub-tasks
   - Select appropriate tools
   - Execute analysis steps
   - Reflect on and refine responses
4. View the reasoning trace in debug mode

### 6. User Settings

Access settings by clicking the ⚙️ icon in the sidebar:

- **Profile Tab** — Edit user information
- **Security Tab** — Change password, delete account
- **Preferences Tab** — Configure feature visibility and behavior
- **Data Tab** — Export conversation history as JSON

### 7. Chat History

- Conversations are automatically saved
- Access via the sidebar, organized by date
- Search conversations by keyword
- Delete or archive conversations as needed
- Restore starred conversations

---

## Security and Privacy

### Data Protection

- All user data is processed locally within the application
- Uploaded datasets are stored only on your server
- Raw file data is never transmitted to external services
- Only processed summarization text is sent to the Groq LLM API

### Authentication Security

- Passwords are hashed using bcrypt (workfactor: 12)
- Session tokens are cryptographically generated
- Automatic session expiration after configured timeout
- CSRF protection on all state-changing operations

### Access Control

- Per-user data isolation at the database level
- Users can only access their own datasets and conversations
- Admin debug features restricted to development mode

### Compliance Considerations

- GDPR-compatible data deletion (permanent removal from SQLite)
- User data export available on demand
- No third-party data sharing
- Minimal telemetry (LangSmith observability is optional)

---

## Troubleshooting

### Common Issues and Solutions

#### Application won't start

```bash
# Verify Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Clear cache
rm -rf __pycache__ .streamlit/
```

#### Groq API authentication error

```
Error: "Could not authenticate with Groq API"
```

**Solution:**
1. Verify `GROQ_API_KEY` in `.env` is correct
2. Check API key has not expired at console.groq.com
3. Ensure firewall allows outbound connections to api.groq.com

#### Vector store initialization fails

```bash
# Reset embeddings cache
rm -rf data/vector_store/*

# Reinitialize
python -c "from rag.knowledge_base import initialize_kb; initialize_kb()"
```

#### Database locked error

```
sqlite3.OperationalError: database is locked
```

**Solution:**
1. Ensure only one Streamlit instance is running
2. Kill previous processes: `pkill -f streamlit`
3. Delete database lock: `rm -f vishleshak.db-wal`

#### Memory issues with large datasets

**Solution:**
1. Increase chunk size in `config/rag_config.py`
2. Reduce `RETRIEVAL_K` value
3. Use `CHUNK_OVERLAP` wisely (default: 100)
4. Consider dataset splitting for very large files (>500MB)

#### Slow query responses

**Optimization steps:**
1. Check CHUNK_SIZE configuration (1000 recommended)
2. Verify vector store is built: `data/vector_store/` should exist
3. Monitor system RAM using `top` (Linux) or Task Manager (Windows)
4. Consider reducing dataset size

### Debug Mode

Enable debug mode in `.env`:

```env
DEBUG=true
LANGCHAIN_TRACING_V2=true
```

View detailed logs:

```bash
streamlit run app.py --logger.level=debug
```

---

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Set up development environment with test dependencies
4. Make changes following existing code style
5. Test thoroughly before submitting PR
6. Submit pull request with clear description

### Code Standards

- Follow PEP 8 ("black" code formatter)
- Add docstrings to all functions and classes
- Include type hints where applicable
- Write unit tests for new features
- Keep functions focused and modular

### Pull Request Process

1. Update README.md if adding features
2. Increment version in `app.py` docstring
3. Ensure all tests pass
4. Request review from maintainers
5. Address feedback before merging

---

## License

This project is licensed under the MIT License. See LICENSE file for details.

---

## Support and Contact

For issues, feature requests, or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review existing GitHub issues
3. Create a new issue with detailed description
4. Contact the development team

---

**Last Updated:** March 2026
**Version:** 1.0.0
**Maintainer:** Vishleshak AI Development Team

**Made with ❤️ for better financial insights**
#   V I S H L E S H A K . A I 
 
 