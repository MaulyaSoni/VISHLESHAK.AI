"""
Kaggle API — Dataset search and download
==========================================
Integration with Kaggle datasets
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

router = APIRouter()

# ─────────────────────────────────────────────
#  REQUEST MODELS
# ─────────────────────────────────────────────

class KaggleSearchRequest(BaseModel):
    query: str
    size: int = 10

class KaggleDownloadRequest(BaseModel):
    dataset_slug: str

# ─────────────────────────────────────────────
#  KAGGLE SEARCH
# ─────────────────────────────────────────────

@router.post("/kaggle/search")
async def search_kaggle(request: KaggleSearchRequest):
    """Search Kaggle for datasets"""
    try:
        import kaggle
        
        # Authenticate
        kaggle.api.authenticate()
        
        # Search datasets
        datasets = kaggle.api.datasets_list(
            search=request.query,
            sort_by='hottest',
            size=min(request.size, 20)
        )
        
        results = []
        for ds in datasets[:request.size]:
            results.append({
                'slug': ds.ref,
                'title': ds.title,
                'description': ds.description[:300] if ds.description else '',
                'votes': int(ds.totalVotes) if hasattr(ds, 'totalVotes') else 0,
                'downloads': int(ds.totalDownloads) if hasattr(ds, 'totalDownloads') else 0,
                'url': f"https://kaggle.com/datasets/{ds.ref}"
            })
        
        return {
            'status': 'success',
            'query': request.query,
            'count': len(results),
            'datasets': results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kaggle search failed: {str(e)}"
        )

# ─────────────────────────────────────────────
#  KAGGLE DOWNLOAD
# ─────────────────────────────────────────────

@router.post("/kaggle/download")
async def download_kaggle_dataset(request: KaggleDownloadRequest):
    """Download a Kaggle dataset"""
    try:
        import kaggle
        import zipfile
        from pathlib import Path
        
        # Authenticate
        kaggle.api.authenticate()
        
        # Create download directory
        download_dir = Path("kaggle_data") / request.dataset_slug.replace('/', '_')
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Download dataset
        kaggle.api.dataset_download_files(
            request.dataset_slug,
            path=str(download_dir),
            unzip=True
        )
        
        # List downloaded files
        files = list(download_dir.rglob('*'))
        files = [f for f in files if f.is_file()]
        csv_files = [f for f in files if f.suffix.lower() == '.csv']
        
        return {
            'status': 'success',
            'dataset_slug': request.dataset_slug,
            'directory': str(download_dir),
            'files_count': len(files),
            'csv_files': [f.name for f in csv_files],
            'primary_csv': csv_files[0].name if csv_files else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Download failed: {str(e)}"
        )
