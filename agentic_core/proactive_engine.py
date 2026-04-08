"""
Proactive Insight Engine - Background Agent
Runs silently on dataset load to detect anomalies vs past sessions
"""

import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


def run_proactive_scan(state: dict) -> List[str]:
    """
    Run proactive scan on current dataset vs past memory
    
    Returns list of flags/insights
    """
    df = state.get("dataset")
    if df is None:
        return []
    
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "")
    flags = []
    
    try:
        memory_dir = os.path.join("data", "memory", user_id)
        if not os.path.exists(memory_dir):
            return flags
        
        past_files = [f for f in os.listdir(memory_dir) if f.endswith(".json")]
        
        for past_file in past_files:
            if past_file == f"{session_id}.json":
                continue
            
            try:
                with open(os.path.join(memory_dir, past_file), "r") as f:
                    past_data = json.load(f)
                
                similar_flags = _compare_datasets(df, past_data.get("meta", {}))
                flags.extend(similar_flags)
                
            except Exception as e:
                logger.debug(f"Skipping {past_file}: {e}")
        
        new_flags = _detect_new_anomalies(df)
        flags.extend(new_flags)
        
        flags = list(set(flags))[:5]
        
        logger.info(f"🔔 Proactive scan found {len(flags)} flags")
    
    except Exception as e:
        logger.warning(f"Proactive scan error: {e}")
    
    return flags


def _compare_datasets(current_df: pd.DataFrame, past_meta: dict) -> List[str]:
    """Compare current dataset to past dataset"""
    flags = []
    
    if not past_meta:
        return flags
    
    current_shape = current_df.shape
    past_shape = past_meta.get("shape", [0, 0])
    
    if current_shape[0] != past_shape[0]:
        row_diff = current_shape[0] - past_shape[0]
        if abs(row_diff) / max(past_shape[0], 1) > 0.2:
            flags.append(f"Dataset row count changed by {row_diff:+d} ({row_diff/max(past_shape[0],1)*100:+.1f}%)")
    
    current_cols = set(current_df.columns)
    past_cols = set(past_meta.get("columns", []))
    
    new_cols = current_cols - past_cols
    if new_cols:
        flags.append(f"New columns detected: {', '.join(list(new_cols)[:3])}")
    
    dropped_cols = past_cols - current_cols
    if dropped_cols:
        flags.append(f"Columns removed: {', '.join(list(dropped_cols)[:3])}")
    
    return flags


def _detect_new_anomalies(df: pd.DataFrame) -> List[str]:
    """Detect statistical anomalies in the data"""
    flags = []
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    for col in numeric_cols[:5]:
        try:
            data = df[col].dropna()
            if len(data) < 10:
                continue
            
            z_scores = np.abs(stats.zscore(data))
            outlier_count = (z_scores > 3).sum()
            outlier_pct = outlier_count / len(data) * 100
            
            if outlier_pct > 5:
                flags.append(f"High outliers in '{col}' ({outlier_pct:.1f}% of data)")
            
            null_pct = df[col].isnull().sum() / len(df) * 100
            if null_pct > 20:
                flags.append(f"High missing values in '{col}' ({null_pct:.1f}%)")
            
            if data.min() < 0 and data.mean() > 0:
                neg_count = (data < 0).sum()
                flags.append(f"Contains {neg_count} negative values in '{col}'")
        
        except Exception:
            continue
    
    return flags


def save_proactive_memory(state: dict, flags: List[str]):
    """Save current dataset metadata for future comparisons"""
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "")
    
    try:
        memory_dir = os.path.join("data", "memory", user_id)
        os.makedirs(memory_dir, exist_ok=True)
        
        df = state.get("dataset")
        meta = {
            "shape": list(df.shape) if df is not None else [0, 0],
            "columns": list(df.columns) if df is not None else [],
            "dtypes": df.dtypes.astype(str).to_dict() if df is not None else {},
            "saved_at": datetime.now().isoformat(),
            "proactive_flags": flags
        }
        
        memory_file = os.path.join(memory_dir, f"{session_id}.json")
        with open(memory_file, "w") as f:
            json.dump({"meta": meta, "summary": state.get("insights_text", "")[:500]}, f)
        
        logger.info(f"✅ Saved proactive memory: {memory_file}")
    
    except Exception as e:
        logger.warning(f"Failed to save memory: {e}")