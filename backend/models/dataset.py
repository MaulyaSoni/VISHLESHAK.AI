"""
Dataset models
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Dataset:
    """Dataset model"""
    hash: str
    filename: str
    rows: int
    cols: int
    meta: Dict[str, Any]
    filepath: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'hash': self.hash,
            'filename': self.filename,
            'rows': self.rows,
            'cols': self.cols,
            'meta': self.meta
        }


@dataclass
class DatasetUploadResponse:
    """Dataset upload response"""
    dataset_hash: str
    filename: str
    rows: int
    cols: int
    meta: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            'dataset_hash': self.dataset_hash,
            'filename': self.filename,
            'rows': self.rows,
            'cols': self.cols,
            'meta': self.meta
        }
