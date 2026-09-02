"""
Models API — ML model management endpoints
===========================================
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path

router = APIRouter()

# ─────────────────────────────────────────────
#  MODELS
# ─────────────────────────────────────────────
class ModelRequest(BaseModel):
    instruction: str
    model_type: str = "xgboost"  # xgboost, random_forest, linear_regression
    target_column: Optional[str] = None
    features: Optional[List[str]] = None

class PredictionRequest(BaseModel):
    model_id: str
    data: dict

class ModelResponse(BaseModel):
    model_id: str
    status: str
    metrics: Optional[dict] = None

# In-memory model storage (use DB in production)
models_db = {}

# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@router.post("/models/train", response_model=ModelResponse)
async def train_model(request: ModelRequest):
    """Train a new ML model"""
    model_id = f"model_{len(models_db) + 1}"
    
    # Placeholder — integrate with actual training logic
    models_db[model_id] = {
        'model_id': model_id,
        'instruction': request.instruction,
        'model_type': request.model_type,
        'status': 'trained',
        'metrics': {
            'accuracy': 0.85,
            'mse': 0.12
        }
    }
    
    return ModelResponse(
        model_id=model_id,
        status='trained',
        metrics=models_db[model_id]['metrics']
    )

@router.post("/models/predict")
async def predict(request: PredictionRequest):
    """Make prediction using trained model"""
    if request.model_id not in models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Placeholder prediction
    return {
        'prediction': 0.75,
        'confidence': 0.89,
        'model_id': request.model_id
    }

@router.get("/models")
async def list_models():
    """List all trained models"""
    return list(models_db.values())

@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get model details"""
    if model_id not in models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    return models_db[model_id]

@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """Delete a model"""
    if model_id not in models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    del models_db[model_id]
    return {'status': 'deleted', 'model_id': model_id}
