# FINBOT v4 - Phase 2 Integration Guide

## Phase 2: Sequential Reasoning & Chain-of-Thought

**Status:** ✅ Complete and Tested

This document explains how to integrate the Phase 2 sequential reasoning system into your FINBOT application.

---

## 📋 What Was Implemented

### Core Components

1. **Chain Configuration** (`config/chain_config.py`)
   - Settings for all chain types
   - Decomposition thresholds
   - Chain-of-thought parameters
   - Memory integration strategies

2. **Question Decomposer** (`chatbot/question_decomposer.py`)
   - 3 decomposition strategies: simple, smart, LLM-based
   - Complexity detection
   - Answer recomposition
   - Dependency tracking

3. **Chain-of-Thought Reasoner** (`chatbot/cot_reasoner.py`)
   - 6-step reasoning process
   - Memory integration
   - Confidence scoring
   - Formatted output for display

4. **Sequential Chain Manager** (`chatbot/sequential_chain.py`)
   - 5 chain types with auto-detection
   - Execution orchestration
   - Statistics tracking
   - Fallback handling

5. **Test Suite** (`tests/test_phase2_sequential.py`)
   - 15 comprehensive tests
   - All components verified
   - Memory integration tested

---

## 🚀 Quick Start

### 1. Run Tests

```powershell
cd d:\FINBOT-2\finbot-clean
python tests/test_phase2_sequential.py
```

Expected output:
```
✅ ALL PHASE 2 TESTS PASSED!

Phase 2 Components Verified:
  ✅ Question decomposition (3 strategies)
  ✅ Chain-of-thought reasoning (6 steps)
  ✅ Sequential chain manager (5 chain types)
  ✅ Memory integration (Phase 1 + Phase 2)
```

### 2. Basic Usage

```python
from chatbot.sequential_chain import get_sequential_chain_manager
from core.enhanced_memory import get_enhanced_memory_manager

# Initialize memory (Phase 1)
memory = get_enhanced_memory_manager()

# Initialize chain manager (Phase 2)
chain_manager = get_sequential_chain_manager(memory)

# Execute reasoning chain
result = chain_manager.execute(
    question="What was revenue last quarter and how does it compare to this quarter?",
    data_context=your_data_string
)

print(result['answer'])
```

---

## 🔧 Integration with Existing app.py

### Option 1: Minimal Integration (Recommended)

Replace your existing question-answering logic in `app.py`:

```python
# Add imports at top
from chatbot.sequential_chain import get_sequential_chain_manager, ChainType
from core.enhanced_memory import get_enhanced_memory_manager

# Initialize in your setup (after existing initialization)
if 'enhanced_memory' not in st.session_state:
    st.session_state.enhanced_memory = get_enhanced_memory_manager()

if 'chain_manager' not in st.session_state:
    st.session_state.chain_manager = get_sequential_chain_manager(
        st.session_state.enhanced_memory
    )

# In your chat function, replace the old QA chain with:
def answer_question(question, data_context):
    """Answer question using sequential reasoning"""
    
    # Execute chain
    result = st.session_state.chain_manager.execute(
        question=question,
        data_context=data_context
    )
    
    # Save to memory
    st.session_state.enhanced_memory.add_turn(
        user_message=question,
        assistant_message=result['answer'],
        data_context=data_context
    )
    
    return result['answer']
```

### Option 2: Advanced Integration (Full Features)

For maximum control and visibility:

```python
def answer_question_advanced(question, data_context):
    """Advanced answer with chain type control and reasoning display"""
    
    # Auto-detect or let user choose chain type
    chain_type = st.session_state.chain_manager._detect_chain_type(question)
    
    # Show what chain will be used
    st.info(f"Using {chain_type.value} reasoning chain")
    
    # Execute
    result = st.session_state.chain_manager.execute(
        question=question,
        data_context=data_context,
        chain_type=chain_type  # or None for auto-detection
    )
    
    # Display reasoning steps if available
    if result.get('reasoning_visible') and 'steps' in result:
        with st.expander("🧠 Reasoning Process"):
            for step in result['steps']:
                st.write(f"**{step['name'].title()}:** {step['result']}")
    
    # Show confidence if available
    if 'confidence' in result:
        st.metric("Confidence", f"{result['confidence']:.1%}")
    
    # Save to memory
    st.session_state.enhanced_memory.add_turn(
        user_message=question,
        assistant_message=result['answer'],
        data_context=data_context
    )
    
    return result['answer']
```

### Option 3: Side-by-Side Comparison

Keep your old system and compare:

```python
# Toggle between old and new system
use_advanced_reasoning = st.sidebar.checkbox("Use Advanced Reasoning (Phase 2)", value=True)

if use_advanced_reasoning:
    answer = answer_question_advanced(question, data_context)
else:
    answer = old_qa_chain(question, data_context)
```

---

## 📊 Chain Types Explained

### 1. Simple Chain
- **When:** Straightforward factual questions
- **Example:** "What is the total revenue?"
- **Process:** Direct answer from data

### 2. Sequential Chain
- **When:** Multi-step operations
- **Example:** "Calculate profit margin"
- **Process:** Understand → Retrieve → Reason

### 3. Decomposition Chain
- **When:** Multi-part questions
- **Example:** "What is revenue, expenses, and profit?"
- **Process:** Break into sub-questions → Answer each → Recompose

### 4. Chain-of-Thought Chain
- **When:** Analytical questions
- **Example:** "Why did revenue increase?"
- **Process:** 6-step reasoning with explicit thinking

### 5. Memory-Augmented Chain
- **When:** Questions referencing history
- **Example:** "Compare to last time we analyzed this"
- **Process:** Comprehensive memory retrieval → Reason with context

---

## ⚙️ Configuration

### Adjust Chain Behavior

Edit `config/chain_config.py`:

```python
# Show reasoning steps to users
SHOW_REASONING_STEPS = True  # False to hide thinking process

# Complexity threshold for decomposition
COMPLEXITY_THRESHOLD = 0.7  # Lower = more sensitive (0.0-1.0)

# Fallback behavior
FALLBACK_TO_SIMPLE = True  # True to fallback on errors

# Memory integration strategy
MEMORY_INTEGRATION_STRATEGY = "adaptive"  # conservative/adaptive/aggressive
```

### Adjust Memory Settings

Edit `config/memory_config.py`:

```python
# Short-term memory size
SHORT_TERM_BUFFER_SIZE = 10  # Last N conversations

# Consolidation trigger
CONSOLIDATION_TRIGGER_COUNT = 50  # Consolidate every N conversations

# Importance threshold
IMPORTANCE_THRESHOLD = 0.6  # Higher = stricter filtering
```

---

## 📈 Monitoring and Statistics

### View Chain Statistics

```python
# Get execution statistics
stats = st.session_state.chain_manager.get_statistics()

st.write(f"Total executions: {stats['total_executions']}")
st.write(f"Average time: {stats['avg_execution_time']:.2f}s")

# By chain type
for chain_type, data in stats['by_chain_type'].items():
    st.write(f"{chain_type}: {data['count']} executions, avg {data['avg_time']:.2f}s")
```

### View Memory Statistics

```python
# Get memory statistics
memory_stats = st.session_state.enhanced_memory.get_statistics()

st.write(f"Total conversations: {memory_stats['total_conversations']}")
st.write(f"Semantic facts: {memory_stats['semantic_memories']}")
st.write(f"Important episodes: {memory_stats['episodic_memories']}")
```

---

## 🧪 Testing

### Run Full Test Suite

```powershell
# Phase 1 tests (memory system)
python tests/test_phase1_memory.py

# Phase 2 tests (reasoning chains)
python tests/test_phase2_sequential.py

# Quick verification
python tests/test_phase1_quick.py
```

### Manual Testing Scenarios

1. **Simple Question**
   ```
   User: "What is the total revenue?"
   Expected: Quick direct answer
   ```

2. **Complex Multi-part**
   ```
   User: "What is revenue, expenses, and net profit margin?"
   Expected: Decomposition into 3 sub-questions
   ```

3. **Analytical**
   ```
   User: "Why did the profit increase this quarter?"
   Expected: Chain-of-thought reasoning with explanation
   ```

4. **Memory Reference**
   ```
   User: "How does this compare to our previous analysis?"
   Expected: Memory-augmented answer referencing history
   ```

---

## 🎯 Best Practices

### 1. Memory Management

```python
# Periodically consolidate memory
if conversation_count % 50 == 0:
    st.session_state.enhanced_memory.consolidate_memories()

# Clear old short-term memory when sessions reset
if st.button("New Session"):
    st.session_state.enhanced_memory.clear_short_term()
```

### 2. Error Handling

```python
try:
    result = chain_manager.execute(question, data_context)
except Exception as e:
    st.error(f"Reasoning error: {e}")
    # Fallback to simple answer
    result = chain_manager.execute(
        question, 
        data_context, 
        chain_type=ChainType.SIMPLE
    )
```

### 3. Performance Optimization

```python
# Use simple chain for quick responses
if len(question) < 20:
    chain_type = ChainType.SIMPLE
else:
    chain_type = None  # Auto-detect

result = chain_manager.execute(question, data_context, chain_type)
```

---

## 🔍 Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Or specific components
logging.getLogger('chatbot.sequential_chain').setLevel(logging.DEBUG)
logging.getLogger('chatbot.cot_reasoner').setLevel(logging.DEBUG)
```

### Inspect Reasoning Steps

```python
result = chain_manager.execute(question, data_context)

# Print all steps
for step in result['steps']:
    print(f"{step['name']}: {step['result']}")

# Check metadata
print(f"Chain type: {result['metadata']['chain_type']}")
print(f"Execution time: {result['metadata']['execution_time']:.2f}s")
```

---

## 📚 API Reference

### SequentialChainManager

```python
chain_manager = get_sequential_chain_manager(memory_manager)

# Execute chain
result = chain_manager.execute(
    question: str,                      # User's question
    data_context: str,                 # Available data
    chain_type: Optional[ChainType],   # Force specific chain
    chat_history: Optional[List]       # Chat history
) -> Dict[str, Any]

# Returns:
{
    'answer': str,                     # Final answer
    'reasoning_visible': bool,         # Is reasoning shown?
    'steps': List[Dict],               # Reasoning steps
    'confidence': float,               # Confidence score (0-1)
    'metadata': {
        'chain_type': str,
        'execution_time': float,
        'timestamp': str
    }
}
```

### QuestionDecomposer

```python
decomposer = get_question_decomposer()

# Decompose question
sub_questions = decomposer.decompose(
    question: str,
    method: str = "auto"  # auto/simple/smart/llm
) -> List[Dict]

# Recompose answers
final_answer = decomposer.recompose_answer(
    sub_answers: List[Dict],
    original_question: str
) -> str
```

### ChainOfThoughtReasoner

```python
reasoner = get_cot_reasoner(memory_manager)

# Execute reasoning
result = reasoner.reason(
    question: str,
    data_context: str,
    chat_history: Optional[List]
) -> Dict[str, Any]

# Format for display
formatted = reasoner.format_reasoning_for_display(result)
```

---

## 🎓 Example: Complete Integration

Here's a complete example integrating Phase 1 + Phase 2 into a Streamlit app:

```python
import streamlit as st
from chatbot.sequential_chain import get_sequential_chain_manager, ChainType
from core.enhanced_memory import get_enhanced_memory_manager

def initialize_session():
    """Initialize session state"""
    if 'enhanced_memory' not in st.session_state:
        st.session_state.enhanced_memory = get_enhanced_memory_manager()
    
    if 'chain_manager' not in st.session_state:
        st.session_state.chain_manager = get_sequential_chain_manager(
            st.session_state.enhanced_memory
        )
    
    if 'conversation_count' not in st.session_state:
        st.session_state.conversation_count = 0

def process_question(question, data_context):
    """Process user question with advanced reasoning"""
    
    # Auto-detect chain type
    chain_type = st.session_state.chain_manager._detect_chain_type(question)
    
    # Show chain type
    st.info(f"🧠 Using {chain_type.value} reasoning")
    
    # Execute reasoning
    with st.spinner("Thinking..."):
        result = st.session_state.chain_manager.execute(
            question=question,
            data_context=data_context
        )
    
    # Display reasoning if available
    if result.get('reasoning_visible') and result.get('steps'):
        with st.expander("View Reasoning Steps"):
            for step in result['steps']:
                st.markdown(f"**{step['name'].title()}**")
                st.write(step['result'])
    
    # Display confidence
    if 'confidence' in result:
        st.metric("Confidence", f"{result['confidence']:.0%}")
    
    # Save to memory
    st.session_state.enhanced_memory.add_turn(
        user_message=question,
        assistant_message=result['answer'],
        data_context=data_context
    )
    
    # Increment count
    st.session_state.conversation_count += 1
    
    # Consolidate periodically
    if st.session_state.conversation_count % 50 == 0:
        st.session_state.enhanced_memory.consolidate_memories()
        st.success("Memory consolidated")
    
    return result['answer']

# Streamlit UI
st.title("FINBOT v4 - Advanced AI Chatbot")

initialize_session()

# Sidebar
with st.sidebar:
    st.header("Statistics")
    
    # Chain stats
    stats = st.session_state.chain_manager.get_statistics()
    st.metric("Total Questions", stats['total_executions'])
    st.metric("Avg Response Time", f"{stats['avg_execution_time']:.2f}s")
    
    # Memory stats
    mem_stats = st.session_state.enhanced_memory.get_statistics()
    st.metric("Conversations", mem_stats['total_conversations'])
    st.metric("Semantic Facts", mem_stats['semantic_memories'])

# Main chat
user_input = st.text_input("Ask a question:")
data_context = st.text_area("Data context:", "Your data here...")

if st.button("Submit") and user_input:
    answer = process_question(user_input, data_context)
    st.success(answer)
```

---

## 🚀 Next Steps

1. **Test the System**
   ```powershell
   python tests/test_phase2_sequential.py
   ```

2. **Integrate into app.py**
   - Choose integration option (minimal/advanced/side-by-side)
   - Add imports
   - Replace Q&A logic
   - Test with real data

3. **Customize Configuration**
   - Edit `config/chain_config.py`
   - Adjust `config/memory_config.py`
   - Tune for your use case

4. **Monitor Performance**
   - Track statistics
   - Optimize slow chains
   - Adjust thresholds

---

## ✅ Verification Checklist

- [ ] Phase 2 tests pass (`python tests/test_phase2_sequential.py`)
- [ ] Phase 1 tests pass (`python tests/test_phase1_memory.py`)
- [ ] Integration added to app.py
- [ ] Configuration reviewed and adjusted
- [ ] All 5 chain types tested manually
- [ ] Memory integration verified
- [ ] Statistics tracking confirmed
- [ ] Error handling tested

---

## 📞 Support

If you encounter issues:

1. Check logs: `logging.basicConfig(level=logging.DEBUG)`
2. Verify imports: `python test_imports.py`
3. Run tests: `python tests/test_phase2_sequential.py`
4. Review configuration files

---

## 🎉 Summary

**Phase 2 is complete and ready for production!**

Key Features:
- ✅ 5 chain types with auto-detection
- ✅ Question decomposition (3 strategies)
- ✅ Chain-of-thought reasoning (6 steps)
- ✅ Memory integration (Phase 1 + Phase 2)
- ✅ Statistics tracking
- ✅ Comprehensive test suite

The system is production-ready and fully integrated with Phase 1's multi-tiered memory system.
