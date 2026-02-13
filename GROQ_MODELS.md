# Groq Model Reference for FINBOT v4

## Current Model Configuration

**Updated:** February 14, 2026

The model `llama-3.1-70b-versatile` has been **decommissioned** by Groq.

FINBOT v4 is now configured to use: **`llama-3.3-70b-versatile`**

---

## Available Groq Models (2026)

### Recommended Models

1. **llama-3.3-70b-versatile** ⭐ (Current default)
   - Best for comprehensive analysis
   - High quality insights
   - Good balance of speed and quality

2. **llama-3.1-8b-instant**
   - Faster responses
   - Lower cost
   - Good for Q&A mode

3. **mixtral-8x7b-32768**
   - Large context window (32K tokens)
   - Good for complex analysis
   - Alternative to LLaMA

---

## How to Change Models

### Option 1: Edit config/settings.py

```python
# Line 21-22 in config/settings.py
LLM_MODEL = "llama-3.3-70b-versatile"  # For analysis
CHAT_MODEL = "llama-3.3-70b-versatile"  # For Q&A
```

### Option 2: Environment Variables

Add to your `.env` file:
```bash
LLM_MODEL=llama-3.1-8b-instant
CHAT_MODEL=llama-3.1-8b-instant
```

---

## Model Comparison

| Model | Speed | Quality | Context | Best For |
|-------|-------|---------|---------|----------|
| llama-3.3-70b-versatile | Medium | Excellent | 8K | Deep analysis, insights |
| llama-3.1-8b-instant | Fast | Very Good | 8K | Q&A, quick responses |
| mixtral-8x7b-32768 | Medium | Excellent | 32K | Large datasets, complex queries |

---

## After Changing Models

1. Save the changes to `config/settings.py`
2. Restart the Streamlit app:
   ```bash
   # Stop the current app (Ctrl+C)
   streamlit run app.py
   ```

---

## Check Available Models

Visit: https://console.groq.com/docs/models

Or check deprecations: https://console.groq.com/docs/deprecations

---

## Current Status

✅ **Model updated to:** `llama-3.3-70b-versatile`  
✅ **Should work without API errors**  
✅ **Full functionality maintained**

If you still get errors, try using `llama-3.1-8b-instant` instead.
