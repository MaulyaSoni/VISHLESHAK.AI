"""
File handling service
"""
import os
import hashlib
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from backend.models.dataset import Dataset, DatasetUploadResponse
from backend.config.settings import get_settings
from backend.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class FileService:
    """File handling service"""
    
    ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json'}
    
    def __init__(self):
        self.upload_folder = Path(settings.UPLOAD_FOLDER)
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self._datasets: Dict[str, Dataset] = {}
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Generate hash for file"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_file_metadata(self, filepath: Path) -> Dict[str, Any]:
        """Extract metadata from file"""
        try:
            if filepath.suffix == '.csv':
                df = pd.read_csv(filepath, nrows=1000)
            elif filepath.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath, nrows=1000)
            elif filepath.suffix == '.json':
                df = pd.read_json(filepath)
            else:
                return {'columns': [], 'dtypes': {}}
            
            return {
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'sample_rows': min(1000, len(df))
            }
        except Exception as e:
            logger.error(f"Error reading file metadata: {e}")
            return {'columns': [], 'dtypes': {}, 'error': str(e)}
    
    def save_upload(self, file_storage) -> DatasetUploadResponse:
        """Save uploaded file and return dataset info"""
        # Generate unique filename
        ext = Path(file_storage.filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file type. Allowed: {self.ALLOWED_EXTENSIONS}")
        
        unique_name = f"{uuid.uuid4().hex}{ext}"
        filepath = self.upload_folder / unique_name
        
        # Save file
        file_storage.save(filepath)
        
        # Generate hash and metadata
        file_hash = self._get_file_hash(filepath)
        meta = self._get_file_metadata(filepath)
        
        # Get row count
        try:
            if ext == '.csv':
                df = pd.read_csv(filepath)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath)
            elif ext == '.json':
                df = pd.read_json(filepath)
            rows = len(df)
            cols = len(df.columns)
        except Exception as e:
            logger.error(f"Error counting rows: {e}")
            rows = 0
            cols = 0
        
        # Create dataset record
        dataset = Dataset(
            hash=file_hash,
            filename=file_storage.filename,
            rows=rows,
            cols=cols,
            meta=meta,
            filepath=str(filepath)
        )
        self._datasets[file_hash] = dataset
        
        logger.info(f"File uploaded: {file_storage.filename} ({rows} rows, {cols} cols)")
        
        return DatasetUploadResponse(
            dataset_hash=file_hash,
            filename=file_storage.filename,
            rows=rows,
            cols=cols,
            meta=meta
        )
    
    def get_dataset(self, dataset_hash: str) -> Optional[Dataset]:
        """Get dataset by hash"""
        ds = self._datasets.get(dataset_hash)
        if ds:
            return ds

        # Fallback: reconstruct dataset record by scanning uploads directory.
        # This allows the frontend to continue working after server restarts.
        try:
            for filepath in self.upload_folder.glob("*"):
                if not filepath.is_file():
                    continue
                try:
                    file_hash = self._get_file_hash(filepath)
                except Exception:
                    continue
                if file_hash != dataset_hash:
                    continue

                meta = self._get_file_metadata(filepath)
                try:
                    if filepath.suffix.lower() == ".csv":
                        df = pd.read_csv(filepath)
                    elif filepath.suffix.lower() in [".xlsx", ".xls"]:
                        df = pd.read_excel(filepath)
                    elif filepath.suffix.lower() == ".json":
                        df = pd.read_json(filepath)
                    else:
                        df = None
                    rows = int(len(df)) if df is not None else 0
                    cols = int(len(df.columns)) if df is not None else 0
                except Exception:
                    rows, cols = 0, 0

                ds = Dataset(
                    hash=file_hash,
                    filename=filepath.name,
                    rows=rows,
                    cols=cols,
                    meta=meta,
                    filepath=str(filepath),
                )
                self._datasets[file_hash] = ds
                return ds
        except Exception:
            return None

        return None

    def load_dataframe(self, dataset_hash: str) -> pd.DataFrame:
        """
        Load a dataset DataFrame by dataset hash.

        This is used by chat/analysis endpoints to reliably access the uploaded data
        even if the DataFrame is not cached in memory.
        """
        dataset = self.get_dataset(dataset_hash)
        if not dataset:
            raise FileNotFoundError(f"Unknown dataset_hash: {dataset_hash}")

        filepath = Path(dataset.filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Dataset file missing: {filepath}")

        ext = filepath.suffix.lower()
        if ext == ".csv":
            return pd.read_csv(filepath)
        if ext in [".xlsx", ".xls"]:
            return pd.read_excel(filepath)
        if ext == ".json":
            return pd.read_json(filepath)
        raise ValueError(f"Unsupported dataset file type: {ext}")
    
    def scan_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """Scan folder for data files"""
        files = []
        try:
            folder = Path(folder_path)
            if not folder.exists():
                return files
            
            for ext in self.ALLOWED_EXTENSIONS:
                for filepath in folder.glob(f"*{ext}"):
                    stat = filepath.stat()
                    files.append({
                        'name': filepath.name,
                        'path': str(filepath),
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'modified': stat.st_mtime
                    })
        except Exception as e:
            logger.error(f"Error scanning folder: {e}")
        
        return files
    
    def load_by_path(self, file_path: str) -> DatasetUploadResponse:
        """Load file by absolute path"""
        filepath = Path(file_path)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Create a mock file storage
        class MockFileStorage:
            def __init__(self, path):
                self.filename = path.name
                self.path = path
            
            def save(self, dest):
                import shutil
                shutil.copy(self.path, dest)
        
        mock_file = MockFileStorage(filepath)
        return self.save_upload(mock_file)


# Singleton instance
file_service = FileService()
