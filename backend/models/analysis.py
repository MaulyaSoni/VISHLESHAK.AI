"""
Analysis models
"""
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis status enum"""
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


@dataclass
class AnalysisRequest:
    """Analysis request model"""
    query: str
    dataset_hash: str
    domain: str = "general"
    mode: Literal["analysis_only", "analysis_ml", "analysis_ml_notebook"] = "analysis_only"
    
    def to_dict(self) -> dict:
        return {
            'query': self.query,
            'dataset_hash': self.dataset_hash,
            'domain': self.domain,
            'mode': self.mode
        }


@dataclass
class AnalysisResponse:
    """Analysis response model"""
    session_id: str
    status: AnalysisStatus
    message: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'session_id': self.session_id,
            'status': self.status.value,
            'message': self.message
        }
