"""
Benchmarks API — System performance metrics
=============================================
Track and retrieve system benchmarks
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

router = APIRouter()

# ─────────────────────────────────────────────
#  BENCHMARKS ENDPOINT
# ─────────────────────────────────────────────

@router.get("/benchmarks")
async def get_benchmarks(
    category: str = "all",
    period: str = "week"
):
    """
    Get system benchmarks and performance metrics
    Categories: all, accuracy, speed, quality
    Periods: day, week, month
    """
    try:
        # In production, this would query a database
        # For now, return comprehensive demo data
        
        now = datetime.now()
        
        # Accuracy metrics
        accuracy_metrics = {
            'prediction_accuracy': {
                'current': 0.94,
                'previous': 0.91,
                'change': 0.03,
                'unit': '%'
            },
            'classification_f1': {
                'current': 0.92,
                'previous': 0.89,
                'change': 0.03,
                'unit': 'score'
            },
            'regression_r2': {
                'current': 0.87,
                'previous': 0.84,
                'change': 0.03,
                'unit': 'score'
            }
        }
        
        # Speed metrics
        speed_metrics = {
            'avg_response_time': {
                'current': 1.2,
                'previous': 1.5,
                'change': -0.3,
                'unit': 'seconds'
            },
            'analysis_speed': {
                'current': 3.8,
                'previous': 4.2,
                'change': -0.4,
                'unit': 'seconds per 1K rows'
            },
            'query_latency': {
                'current': 0.45,
                'previous': 0.52,
                'change': -0.07,
                'unit': 'seconds'
            }
        }
        
        # Quality metrics
        quality_metrics = {
            'response_quality': {
                'current': 0.96,
                'previous': 0.93,
                'change': 0.03,
                'unit': 'score'
            },
            'user_satisfaction': {
                'current': 0.89,
                'previous': 0.85,
                'change': 0.04,
                'unit': 'score'
            },
            'code_execution_success': {
                'current': 0.98,
                'previous': 0.96,
                'change': 0.02,
                'unit': '%'
            }
        }
        
        # Historical data (last 7 days)
        historical_data = []
        for i in range(7, 0, -1):
            date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            date = date - timedelta(days=i)
            
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'accuracy': 0.85 + (0.02 * (7 - i)),
                'speed': 1.8 - (0.1 * (7 - i)),
                'quality': 0.88 + (0.02 * (7 - i))
            })
        
        # Build response based on category
        benchmarks = {
            'accuracy': accuracy_metrics,
            'speed': speed_metrics,
            'quality': quality_metrics,
            'historical': historical_data
        }
        
        return {
            'status': 'success',
            'category': category,
            'period': period,
            'benchmarks': benchmarks if category == 'all' else benchmarks.get(category, {}),
            'summary': {
                'overall_performance': 0.94,
                'trending': 'up',
                'total_analyses': 1247,
                'avg_user_rating': 4.7
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark retrieval failed: {str(e)}"
        )

# ─────────────────────────────────────────────
#  UPDATE BENCHMARKS
# ─────────────────────────────────────────────

@router.post("/benchmarks")
async def update_benchmark(
    metric_name: str,
    value: float,
    category: str = "general"
):
    """Record a new benchmark measurement"""
    try:
        # In production, save to database
        timestamp = datetime.now().isoformat()
        
        return {
            'status': 'success',
            'message': f'Benchmark {metric_name} recorded',
            'data': {
                'metric': metric_name,
                'value': value,
                'category': category,
                'timestamp': timestamp
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update benchmark: {str(e)}"
        )
