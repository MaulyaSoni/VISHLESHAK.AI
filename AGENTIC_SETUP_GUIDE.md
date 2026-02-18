# 🤖 Vishleshak AI — Agentic System Setup Guide

## 📦 What's New

Your Vishleshak AI now includes a **complete agentic system** with:

- ✅ **ReAct Agent** — Autonomous reasoning with Thought → Action → Observation loop
- ✅ **8 Specialized Tools** — Statistical analysis, correlation, anomaly detection, charts, trends, forecasting, Python sandbox, and report generation
- ✅ **Advanced RAG** — Multi-query retrieval, contextual compression, ensemble retrieval
- ✅ **Reflection Layer** — Self-correction and confidence scoring
- ✅ **Agent Memory** — Tool usage learning and performance tracking
- ✅ **Smart UI** — Toggle agent mode and show/hide reasoning process

---

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
pip install langgraph prophet scikit-learn statsmodels reportlab openpyxl
```

Or install all at once:
```powershell
pip install -r requirements.txt
```

### 2. Run Vishleshak AI

```powershell
streamlit run app.py
```

### 3. Enable Agent Mode

1. Upload your dataset
2. Switch to **"💬 RAG Chatbot"** mode in the sidebar
3. Check **"🤖 Enable Agentic Mode"**
4. Toggle **"👁️ Show Reasoning Process"** to see agent thinking

---

## 📁 New File Structure

```
finbot-clean/
├─ agentic_core/              # Core agent system
│  ├─ __init__.py
│  ├─ react_agent.py          # Main ReAct agent
│  ├─ agent_memory.py         # Tool learning system
│  ├─ tool_selector.py        # Smart tool selection
│  ├─ reflection_layer.py     # Self-correction
│  └─ prompts/
│     ├─ system_prompt.py
│     ├─ react_prompt.py
│     └─ reflection_prompt.py
│
├─ tools/specialized/         # 8 specialized tools
│  ├─ statistical_tool.py     # Statistical analysis
│  ├─ correlation_tool.py     # Correlation finder
│  ├─ anomaly_detector.py     # Anomaly detection
│  ├─ chart_generator_v2.py   # Chart generation
│  ├─ trend_analyzer.py       # Trend analysis
│  ├─ forecaster.py           # Forecasting
│  ├─ python_sandbox.py       # Python code execution
│  └─ report_generator.py     # PDF/Excel reports
│
├─ rag/advanced/              # Advanced RAG patterns
│  ├─ multi_query.py          # Multi-query retrieval
│  ├─ contextual_compression.py
│  └─ ensemble_retriever.py
│
├─ config/
│  └─ agent_config.py         # Agent configuration
│
└─ app.py                     # Main app (enhanced)
```

---

## 🛠️ 8 Specialized Tools

### 1. **Statistical Analyzer**
- Comprehensive statistical analysis
- Normality tests, outlier detection
- Descriptive statistics

### 2. **Correlation Finder**
- Pearson/Spearman correlations
- Target-specific correlation analysis
- Strength classification

### 3. **Anomaly Detector**
- Isolation Forest algorithm
- Customizable contamination threshold
- Top anomaly ranking

### 4. **Chart Generator**
- Automatic chart type selection
- Line, bar, histogram, scatter plots
- Base64 image output

### 5. **Trend Analyzer**
- Time series decomposition
- Seasonality detection
- Trend strength measurement

### 6. **Forecaster**
- Prophet-based forecasting
- Customizable forecast horizon
- Confidence intervals

### 7. **Python Sandbox**
- Secure code execution
- Timeout protection
- Subprocess isolation

### 8. **Report Generator**
- PDF and Excel exports
- Summary statistics
- Chart embedding

---

## 🎯 How Agent Mode Works

### ReAct Loop

The agent follows a **Thought → Action → Observation** loop:

```
User Question: "What are the correlations in this data?"

Thought: I need to find correlations between numeric variables
Action: correlation_finder
Action Input: {"method": "pearson", "min_correlation": 0.3}
Observation: [correlation results...]

Thought: Now I should check for anomalies
Action: anomaly_detector
Action Input: {"contamination": 0.1}
Observation: [anomaly results...]

Thought: I have enough information to answer
Final Answer: [comprehensive answer based on tool outputs]
```

### Reflection & Self-Correction

After generating an answer, the **Reflection Layer**:
1. Evaluates answer quality (accuracy, completeness, clarity, relevance, evidence)
2. Assigns confidence score (0-100)
3. Suggests improvements if confidence < 70%
4. Triggers retry if confidence < threshold

### Tool Learning

**Agent Memory** tracks:
- Tool success/failure rates
- Average execution time
- Question type → tool mapping
- Performance trends

The agent **gets smarter over time** by learning which tools work best for different questions.

---

## ⚙️ Configuration

Edit `config/agent_config.py` to customize:

```python
# Agent behavior
MAX_ITERATIONS = 15              # Max reasoning steps
MAX_EXECUTION_TIME = 120         # Timeout (seconds)
AGENT_TEMPERATURE = 0.3          # LLM creativity

# Tool selection
SMART_TOOL_SELECTION = True      # Auto-select relevant tools
MAX_TOOLS_PER_QUERY = 5         # Max tools per question
TOOL_SELECTION_STRATEGY = "hybrid"  # "relevance" | "success_rate" | "hybrid"

# Reflection
ENABLE_REFLECTION = True         # Self-correction
MIN_CONFIDENCE_THRESHOLD = 0.7   # Retry if below this
MAX_REFLECTION_RETRIES = 2       # Max retry attempts

# UI
UI_SETTINGS = {
    "show_thinking": "toggle",   # "always" | "never" | "toggle"
    "show_tool_calls": True,
    "show_confidence": True,
}
```

---

## 🧪 Testing

### Quick Test

```python
from agentic_core import create_vishleshak_agent
from tools.specialized import StatisticalAnalyzerTool, CorrelationFinderTool
import pandas as pd

# Load data
df = pd.read_csv("sample_data.csv")

# Create tools
tools = [
    StatisticalAnalyzerTool(df),
    CorrelationFinderTool(df),
]

# Create agent
agent = create_vishleshak_agent(
    tools=tools,
    data_context=f"Dataset: {len(df)} rows × {len(df.columns)} columns"
)

# Ask question
result = agent.run("What are the key statistics and correlations?")

print(result["answer"])
print(f"Confidence: {result['confidence']:.0%}")
print(f"Tools used: {result['tools_used']}")
```

### Run Tests

```powershell
python -m pytest tests/test_agentic.py -v
```

---

## 💡 Usage Tips

### When to Use Agent Mode

✅ **Use Agent Mode when:**
- You need deep multi-step analysis
- Question requires multiple tools
- You want transparent reasoning
- Dataset exploration and discovery

❌ **Use Regular Q&A when:**
- Simple factual questions
- Direct knowledge base queries
- Quick lookups
- Speed is critical

### Optimizing Performance

1. **Enable smart tool selection** — Reduces tool overhead
2. **Adjust max iterations** — Higher for complex questions, lower for speed
3. **Toggle reflection** — Disable for faster responses
4. **Show thinking selectively** — Hide for production, show for debugging

---

## 🔧 Troubleshooting

### Agent Not Initializing
- Check all dependencies installed: `pip install -r requirements.txt`
- Verify imports in app.py (check console for errors)
- Ensure `agentic_core/` and `tools/specialized/` exist

### Tools Failing
- Check dataset has required columns (numeric for stats/correlation)
- Verify sufficient data points (>10 for anomaly detection)
- Review error messages in agent reasoning trace

### Low Confidence Scores
- Add more context to questions
- Ensure dataset quality is good
- Check if tools have required data
- Review reasoning trace for issues

### Slow Performance
- Reduce MAX_ITERATIONS in config
- Disable ENABLE_REFLECTION for speed
- Use fewer tools (adjust MAX_TOOLS_PER_QUERY)
- Consider caching common queries

---

## 🎓 Learn More

### Key Concepts

- **ReAct Pattern**: Reasoning + Acting in synergy
- **Tool Augmentation**: LLMs enhanced with specialized tools
- **Self-Reflection**: Agents that evaluate their own outputs
- **Meta-Learning**: Systems that improve from experience

### Resources

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Tool Use in LLMs](https://python.langchain.com/docs/modules/agents/)

---

## 🚀 Next Steps

1. ✅ **Test basic functionality** — Run simple questions
2. ✅ **Explore tool combinations** — See how agent chains tools
3. ✅ **Tune configuration** — Optimize for your use case
4. ✅ **Monitor performance** — Check agent memory stats
5. ✅ **Provide feedback** — Use thumbs up/down to improve

---

## 🎉 Congratulations!

Your Vishleshak AI is now a **true agentic system** — autonomous, self-correcting, and continuously learning. Enjoy the power of next-gen AI! 🚀

---

**Questions?** Check the code comments or raise an issue in the repository.
