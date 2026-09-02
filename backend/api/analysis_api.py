"""
Analysis API — Quick analysis endpoints
=========================================
Provides fast analysis without full agent pipeline
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "app_modules"))

router = APIRouter()


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def convert_numpy(obj):
    """Recursively convert numpy types to native python types for JSON serialization"""
    import numpy as np

    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        # Handle special float values (inf, -inf, nan) that are not JSON compliant
        if np.isinf(obj) or np.isnan(obj):
            return None  # or could return a string like "Infinity" or "NaN"
        return float(obj)
    if isinstance(obj, (np.ndarray, list, tuple)):
        return [convert_numpy(i) for i in obj]
    if isinstance(obj, dict):
        return {str(k): convert_numpy(v) for k, v in obj.items()}
    if hasattr(obj, 'tolist'):  # Catch other numpy-like objects
        return convert_numpy(obj.tolist())

    return obj


def smart_read_csv(path, nrows: int = None, chunksize: int = None):
    """Auto-detect encoding. Handles Indian financial datasets."""
    import pandas as pd
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    for enc in encodings:
        try:
            # Eagerly test decoding the header and first row to verify the encoding
            pd.read_csv(path, encoding=enc, nrows=2)

            kwargs = {'filepath_or_buffer': path, 'encoding': enc, 'low_memory': False}
            if nrows:     kwargs['nrows'] = nrows
            if chunksize: kwargs['chunksize'] = chunksize
            return pd.read_csv(**kwargs)
        except (UnicodeDecodeError, UnicodeError, Exception):
            continue
    # Absolute fallback
    return pd.read_csv(path, encoding='latin-1')


# ─────────────────────────────────────────────
#  REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    dataset_hash: str
    use_agent_mode: bool = True
    domain: str = "general"


class AnalyzeResponse(BaseModel):
    status: str
    analysis: dict
    charts: list
    insights: list
    executive_summary: str


class ChartRequest(BaseModel):
    dataset_hash: str
    chart_configs: Optional[list] = None


# ─────────────────────────────────────────────
#  QUICK ANALYSIS ENDPOINT
# ─────────────────────────────────────────────

@router.post("/analyze")
async def analyze_dataset(request: AnalyzeRequest):
    """
    Perform quick analysis on uploaded dataset.
    Returns statistical insights, charts, and summary.
    """
    try:
        from app_modules.analyzers.statistical_analyzer import StatisticalAnalyzer
        from app_modules.analyzers.pattern_detector import PatternDetector

        upload_dir = backend_dir / "resources" / "storage" / "uploads"

        # Try exact hash-named file first (naming: <hash>.<ext>)
        dataset_path = None
        for ext in (".csv", ".tsv", ".xlsx"):
            candidate = upload_dir / f"{request.dataset_hash}{ext}"
            if candidate.exists():
                dataset_path = candidate
                break

        # Fallback: scan for any file whose name contains the hash
        if dataset_path is None:
            for f in upload_dir.glob("*"):
                if request.dataset_hash in f.name:
                    dataset_path = f
                    break

        if dataset_path is None:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset not found: {request.dataset_hash}"
            )

        import pandas as pd

        file_size_mb = dataset_path.stat().st_size / (1024 * 1024)
        print(f"DEBUG: Processing file of size {file_size_mb:.2f}MB")

        if file_size_mb > 50:
            print("DEBUG: Large file detected (>50MB). Sampling first 100k rows.")
            chunks = []
            chunk_gen = smart_read_csv(dataset_path, chunksize=10000)
            for chunk in chunk_gen:
                chunks.append(chunk)
                if sum(len(c) for c in chunks) >= 100000:
                    break
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = smart_read_csv(dataset_path)

        analyzer = StatisticalAnalyzer(df)
        stats = analyzer.analyze_all()

        pattern_detector = PatternDetector(df)
        patterns = pattern_detector.detect_all_patterns()

        charts = []

        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        for col in numeric_cols[:5]:  # Limit to 5 charts
            charts.append({
                'type': 'histogram',
                'column': col,
                'title': f'Distribution of {col}',
                'data': df[col].dropna().tolist()
            })

        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr().round(3)
            charts.append({
                'type': 'correlation_matrix',
                'title': 'Feature Correlations',
                'data': corr_matrix.to_dict()
            })

        analysis = {
            'dataset_info': {
                'rows': len(df),
                'columns': len(df.columns),
                'numeric_columns': len(numeric_cols),
                'categorical_columns': len(df.select_dtypes(include=['object']).columns),
                'missing_values': int(df.isnull().sum().sum()),
            },
            'statistics': convert_numpy(stats),
            'patterns': convert_numpy(patterns),
        }

        executive_summary = (
            f"Dataset contains {len(df)} rows and {len(df.columns)} columns. "
            f"Found {len(numeric_cols)} numeric and "
            f"{len(df.select_dtypes(include=['object']).columns)} categorical features. "
            f"Analysis complete."
        )

        response_data = {
            'status': 'success',
            'analysis': analysis,
            'charts': charts,
            'insights': [],
            'executive_summary': executive_summary,
        }

        print("DEBUG: Converting response data to JSON-safe types...")
        safe_data = convert_numpy(response_data)
        print("DEBUG: Conversion complete.")
        return safe_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


# ─────────────────────────────────────────────
#  ANALYSIS STATUS
# ─────────────────────────────────────────────

@router.get("/analyze/status/{dataset_hash}")
async def get_analysis_status(dataset_hash: str):
    """Check if analysis is available for dataset"""
    upload_dir = backend_dir / "resources" / "storage" / "uploads"

    for file in upload_dir.glob("*"):
        if dataset_hash in file.name:
            return {
                'dataset_hash': dataset_hash,
                'status': 'ready',
                'filename': file.name
            }

    raise HTTPException(status_code=404, detail="Dataset not found")


# ─────────────────────────────────────────────
#  CHART GENERATION
# ─────────────────────────────────────────────

@router.post("/analysis/generate-charts")
async def generate_charts(request: ChartRequest):
    """Generate visuals for the dataset"""
    import pandas as pd
    upload_dir = backend_dir / "resources" / "storage" / "uploads"

    dataset_path = None
    for ext in (".csv", ".tsv", ".xlsx"):
        candidate = upload_dir / f"{request.dataset_hash}{ext}"
        if candidate.exists():
            dataset_path = candidate
            break

    if not dataset_path:
        raise HTTPException(status_code=404, detail="Dataset file not found")

    try:
        df = None
        for enc in ['utf-8', 'latin1', 'cp1252']:
            try:
                df = pd.read_csv(dataset_path, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            df = pd.read_csv(dataset_path)

        charts = []
        num_cols = df.select_dtypes(include=['number']).columns.tolist()

        for col in num_cols[:8]:  # Generate up to 8 charts
            charts.append({
                'type': 'histogram',
                'column': col,
                'title': f'Distribution of {col}',
                'data': convert_numpy(df[col].dropna().tolist())
            })

        return {
            "status": "success",
            "charts": charts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")
