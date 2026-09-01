"""
Week 3: History API for FastAPI
Provides conversation and analysis history endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

router = APIRouter(prefix="/history", tags=["History"])

# ─── Response Models ─────────────────────────────

class ConversationItem(BaseModel):
    id: str
    title: str
    created_at: str
    message_count: int

class AnalysisItem(BaseModel):
    id: str
    title: str
    dataset: str
    created_at: str
    status: str

class ConversationList(BaseModel):
    conversations: List[ConversationItem]

class AnalysisList(BaseModel):
    analyses: List[AnalysisItem]

# ─── Endpoints ───────────────────────────────────

@router.get("/conversations", response_model=ConversationList)
async def get_conversations():
    """
    Get user's conversation history
    """
    # TODO: Fetch from database
    # For now, return empty list
    return ConversationList(conversations=[])

@router.post("/conversations")
async def create_conversation(request: Request):
    """
    Create a new conversation session using ChatRepository
    """
    import uuid
    from datetime import datetime
    
    try:
        body = await request.json()
    except Exception:
        body = {}
        
    title = body.get("title", "New Conversation")
    user_id = body.get("user_id", "default")
    dataset_info = body.get("dataset_info")
    
    # Try to use ChatRepository if available
    try:
        from app_modules.database.chat_repository import ChatRepository
        repo = ChatRepository()
        conv = repo.create_conversation(
            user_id=user_id,
            title=title,
            dataset_info=dataset_info
        )
        return {
            "id": conv.id, 
            "conv_id": conv.id, # Support both formats
            "title": conv.title, 
            "created_at": str(conv.created_at)
        }
    except Exception as e:
        print(f"Error saving to DB: {e}")
        # Fallback if DB not available or fails
        conv_id = str(uuid.uuid4())[:8]
        return {
            "id": conv_id,
            "conv_id": conv_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "status": "created (fallback)"
        }

@router.get("/analyses", response_model=AnalysisList)
async def get_analyses():
    """
    Get user's analysis history
    """
    # TODO: Fetch from database
    # For now, return empty list
    return AnalysisList(analyses=[])

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get specific conversation details
    """
    # TODO: Fetch from database
    return {
        "id": conversation_id,
        "messages": [],
        "title": "Sample Conversation"
    }

@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Get specific analysis details
    """
    # TODO: Fetch from database
    return {
        "id": analysis_id,
        "report": {},
        "status": "completed"
    }
