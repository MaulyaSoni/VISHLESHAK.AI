import hashlib
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, HTTPException
from typing import Optional

# Import smart_read_csv from analysis_api
try:
    from .analysis_api import smart_read_csv
except ImportError:
    def smart_read_csv(path: str, nrows: int = None, chunksize: int = None):
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        for enc in encodings:
            try:
                # Eagerly test decoding the header and first row to verify the encoding
                pd.read_csv(path, encoding=enc, nrows=2)
                
                kwargs = {'filepath_or_buffer': path, 'encoding': enc, 'low_memory': False}
                if nrows:     kwargs['nrows'] = nrows
                if chunksize: kwargs['chunksize'] = chunksize
                return pd.read_csv(**kwargs)
            except:
                continue
        return pd.read_csv(path, encoding='latin-1')

router = APIRouter()

@router.get("/datasets/{dataset_hash}/preview")
async def preview_dataset(dataset_hash: str, rows: int = 10):
    # Use the same path as analysis_api.py
    backend_dir = Path(__file__).parent.parent
    upload_dir = backend_dir / "resources" / "storage" / "uploads"
    
    if not upload_dir.exists():
        raise HTTPException(404, "No uploads directory found")

    # Helper to convert numpy and NaN values to native JSON-safe types
    def convert_val(v):
        import pandas as pd
        import numpy as np
        if pd.isna(v):
            return None
        if isinstance(v, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(v)
        if isinstance(v, (np.floating, np.float64, np.float32, np.float16)):
            return float(v)
        return v

    # Search for file matching hash
    # We check both the filename (if it's already hash-named) and the content hash
    for f in upload_dir.glob("**/*.*"):
        if f.suffix not in ('.csv', '.xlsx', '.xls'):
            continue
            
        try:
            # Check if filename is the hash
            if f.stem == dataset_hash:
                if f.suffix == '.csv':
                    df = smart_read_csv(str(f), nrows=rows)
                    full_df = smart_read_csv(str(f))
                else:
                    df = pd.read_excel(f, nrows=rows)
                    full_df = pd.read_excel(f)
                    
                dtypes_dict = {col: str(dtype) for col, dtype in full_df.dtypes.items()}
                missing_dict = {col: int(full_df[col].isnull().sum()) for col in full_df.columns}
                sample_records = [
                    {col: convert_val(row[col]) for col in df.columns}
                    for _, row in df.iterrows()
                ]

                return {
                    "columns":  df.columns.tolist(),
                    "preview":  sample_records,
                    "sample":   sample_records,
                    "dtypes":   dtypes_dict,
                    "missing":  missing_dict,
                    "shape":    [len(full_df), len(full_df.columns)],
                    "filename": f.name,
                }

            # Fallback: check content-based hash (as requested in spec)
            if f.suffix == '.csv':
                cols = pd.read_csv(f, nrows=0).columns.tolist()
                fhash = hashlib.md5(",".join(sorted(cols)).encode()).hexdigest()
                if fhash == dataset_hash:
                    df = smart_read_csv(str(f), nrows=rows)
                    full_df = smart_read_csv(str(f))
                    
                    dtypes_dict = {col: str(dtype) for col, dtype in full_df.dtypes.items()}
                    missing_dict = {col: int(full_df[col].isnull().sum()) for col in full_df.columns}
                    sample_records = [
                        {col: convert_val(row[col]) for col in df.columns}
                        for _, row in df.iterrows()
                    ]

                    return {
                        "columns":  df.columns.tolist(),
                        "preview":  sample_records,
                        "sample":   sample_records,
                        "dtypes":   dtypes_dict,
                        "missing":  missing_dict,
                        "shape":    [len(full_df), len(full_df.columns)],
                        "filename": f.name,
                    }
        except Exception:
            continue

    raise HTTPException(404, f"Dataset {dataset_hash} not found in uploads")
