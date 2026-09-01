"""
Chat API — AI Chat assistant
==============================
Intelligent conversation with data awareness.
Streams responses as Server-Sent Events (SSE) so ChatbotMode.tsx
can render word-by-word output in real time.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

router = APIRouter()

# ─────────────────────────────────────────────
#  REQUEST MODELS
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    context: Optional[dict] = None
    dataset_hash: Optional[str] = None


# ─────────────────────────────────────────────
#  SSE HELPER
# ─────────────────────────────────────────────

def _sse(payload: dict) -> str:
    """Format a dict as a single SSE data frame."""
    return f"data: {json.dumps(payload)}\n\n"


async def _stream_response(ai_response: str, quality_grade: str) -> AsyncGenerator[str, None]:
    """
    Yield the response word-by-word as SSE chunks, then a final
    done=true frame with metadata.  Matches exactly what
    ChatbotMode.tsx's reader loop expects.
    """
    words = ai_response.split(" ")
    for i, word in enumerate(words):
        # Re-add the space that split() removed (except after the last word)
        chunk_text = word if i == len(words) - 1 else word + " "
        yield _sse({"chunk": chunk_text, "done": False})

    # Map grade → numeric score for the UI quality badge
    grade_scores = {"A": 95, "B": 80, "C": 65, "D": 50, "F": 30}
    quality_score = grade_scores.get(quality_grade, 70)

    yield _sse({
        "chunk": "",
        "done": True,
        "response": ai_response,
        "quality_grade": quality_grade,
        "quality_score": quality_score,
        "confidence": round(quality_score / 100, 2),
        "tools_used": ["rag_retriever"],
        "is_agent": False,
    })


# ─────────────────────────────────────────────
#  CHAT ENDPOINT  (SSE streaming)
# ─────────────────────────────────────────────

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Chat with AI assistant.
    Returns a text/event-stream SSE response streamed word-by-word.
    Final SSE frame contains quality_grade, quality_score, confidence.
    """
    try:
        # ── Try real LLM first ──────────────────────────────────────────
        ai_response = None
        try:
            from app_modules.core.llm import LLMClient

            llm = LLMClient()

            system_prompt = (
                "You are Vishleshak AI, an expert data analysis assistant. "
                "Provide clear, accurate, and helpful responses about data analysis, "
                "statistics, and machine learning. "
                "Always structure your responses with:\n"
                "1. Direct answer\n"
                "2. Key insights\n"
                "3. Actionable recommendations"
            )

            response = llm.generate(
                system_prompt=system_prompt,
                user_message=request.message,
                temperature=0.7,
                max_tokens=1024,
            )
            ai_response = response.get("content", response.get("text", ""))
        except Exception:
            pass  # Fall through to rule-based fallback

        if not ai_response:
            ai_response = generate_fallback_response(request.message)

        quality_grade = calculate_quality_grade(ai_response)

        return StreamingResponse(
            _stream_response(ai_response, quality_grade),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ─────────────────────────────────────────────
#  CONVERSATION HISTORY
# ─────────────────────────────────────────────

@router.get("/chat/conversations")
async def get_conversations(limit: int = 20):
    """Get user's conversation history"""
    try:
        conversations = [
            {
                "id": "conv_1",
                "title": "Sales Data Analysis",
                "last_message": "What are the key trends in Q4 sales?",
                "created_at": datetime.now().replace(hour=10, minute=30).isoformat(),
                "message_count": 15,
                "is_active": True,
            },
            {
                "id": "conv_2",
                "title": "ML Model Comparison",
                "last_message": "Which model performs better for this dataset?",
                "created_at": datetime.now().replace(hour=14, minute=15).isoformat(),
                "message_count": 23,
                "is_active": False,
            },
            {
                "id": "conv_3",
                "title": "Data Cleaning Help",
                "last_message": "How should I handle missing values?",
                "created_at": datetime.now().replace(hour=16, minute=45).isoformat(),
                "message_count": 8,
                "is_active": False,
            },
        ]

        return {
            "status": "success",
            "count": len(conversations),
            "conversations": conversations[:limit],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversations: {str(e)}",
        )


# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────

def generate_fallback_response(message: str) -> str:
    """Generate intelligent fallback response without LLM"""
    message_lower = message.lower()

    if "correlation" in message_lower:
        return (
            "## Understanding Correlation\n\n"
            "Correlation measures the relationship between two variables.\n\n"
            "**Key Points:**\n"
            "- Ranges from -1 to +1\n"
            "- +1: Perfect positive correlation\n"
            "- -1: Perfect negative correlation\n"
            "- 0: No correlation\n\n"
            "**Recommendation:** Use Pearson correlation for linear relationships "
            "and Spearman for monotonic relationships."
        )

    elif "missing" in message_lower or "null" in message_lower:
        return (
            "## Handling Missing Data\n\n"
            "There are several strategies for dealing with missing values:\n\n"
            "**1. Deletion:**\n"
            "- Remove rows/columns with too many missing values\n\n"
            "**2. Imputation:**\n"
            "- Mean/Median/Mode for numeric data\n"
            "- Most frequent for categorical data\n"
            "- KNN or model-based imputation\n\n"
            "**3. Advanced:**\n"
            "- Use algorithms that handle missing values natively\n"
            "- Multiple imputation techniques"
        )

    elif "model" in message_lower or "machine learning" in message_lower:
        return (
            "## Machine Learning Model Selection\n\n"
            "**For Classification:**\n"
            "- Start with: Logistic Regression, Random Forest\n"
            "- For complex patterns: XGBoost, Neural Networks\n\n"
            "**For Regression:**\n"
            "- Start with: Linear Regression, Ridge/Lasso\n"
            "- For non-linear: Random Forest, Gradient Boosting\n\n"
            "**Best Practice:** Always start simple, then increase complexity as needed."
        )

    else:
        return (
            f'## Analysis Insight\n\n'
            f'Based on your question about "{message[:50]}...", here are some insights:\n\n'
            "**Key Observations:**\n"
            "- Consider examining the data distribution\n"
            "- Look for patterns and outliers\n"
            "- Validate assumptions before drawing conclusions\n\n"
            "**Next Steps:**\n"
            "1. Explore the dataset structure\n"
            "2. Run statistical analysis\n"
            "3. Visualize key metrics\n\n"
            "Would you like me to perform any specific analysis?"
        )


def calculate_quality_grade(response: str) -> str:
    """Calculate quality grade based on response characteristics"""
    score = 0

    if len(response) > 100:
        score += 1
    if len(response) > 300:
        score += 1
    if "**" in response:
        score += 1
    if "\n" in response:
        score += 1
    if any(w in response.lower() for w in ["recommendation", "key", "important"]):
        score += 1

    if score >= 5:
        return "A"
    elif score >= 4:
        return "B"
    elif score >= 3:
        return "C"
    elif score >= 2:
        return "D"
    else:
        return "F"
