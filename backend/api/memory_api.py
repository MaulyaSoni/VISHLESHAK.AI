from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List

from backend.app_modules.memory_system.context_persistence import load_context, save_context
from backend.app_modules.memory_system.episodic_store import recall_recent

router = APIRouter()

class BusinessProfileUpdate(BaseModel):
    sector: str = "general"
    fiscal_year_start: str = "April"
    regulatory_framework: str = "None"
    currency: str = "INR"

class PreferencesUpdate(BaseModel):
    insight_verbosity: str = "normal"
    preferred_charts: List[str] = []

class ProfileUpdate(BaseModel):
    business_profile: BusinessProfileUpdate = None
    preferences: PreferencesUpdate = None
    custom_kpis: Dict[str, str] = None

@router.get("/memory/profile")
async def get_profile(user_id: str = "default"):
    return load_context(user_id)

@router.put("/memory/profile")
async def update_profile(update: ProfileUpdate, user_id: str = "default"):
    ctx = load_context(user_id)
    if update.business_profile:
        ctx["business_profile"] = update.business_profile.dict()
    if update.preferences:
        ctx["preferences"] = update.preferences.dict()
    if update.custom_kpis is not None:
        ctx["custom_kpis"] = update.custom_kpis
    save_context(user_id, ctx)
    return {"status": "success", "profile": ctx}

@router.get("/memory/analyses")
async def get_analyses(sector: str = "", limit: int = 20, user_id: str = "default"):
    return recall_recent(user_id, sector=sector, limit=limit)

@router.get("/memory/kpi_trends")
async def get_kpi_trends(user_id: str = "default"):
    ctx = load_context(user_id)
    return ctx.get("kpi_history", {})
