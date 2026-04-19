"""
File routes
"""
import os
from flask import Blueprint, request, jsonify
from backend.services.file_service import file_service
from backend.core.logger import get_logger

logger = get_logger(__name__)
files_bp = Blueprint('files', __name__)


@files_bp.route('/upload', methods=['POST'])
def upload_file():
    """POST /api/files/upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Use the canonical backend file service so dataset_hash is stable
        # and the dataset can be loaded later by hash.
        upload = file_service.save_upload(file)

        # Compute a few convenience fields used by the frontend UI.
        import pandas as pd
        df = file_service.load_dataframe(upload.dataset_hash)
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        missing_pct = round(
            df.isnull().sum().sum() / max(1, df.shape[0] * df.shape[1]) * 100,
            1,
        )

        return jsonify({
            "dataset_hash": upload.dataset_hash,
            "filename": upload.filename,
            "rows": upload.rows,
            "cols": upload.cols,
            "numeric_count": len(numeric_cols),
            "categorical_count": len(cat_cols),
            "missing_pct": missing_pct,
            "meta": {
                **(upload.meta or {}),
                "columns": df.columns.tolist(),
                "numeric_columns": numeric_cols,
                "categorical_columns": cat_cols,
            },
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500


@files_bp.route('/scan', methods=['POST'])
def scan_folder():
    """POST /api/files/scan"""
    data = request.get_json()
    folder_path = data.get('folder_path', '')
    
    if not folder_path:
        return jsonify({'error': 'Folder path required'}), 400
    
    try:
        files = file_service.scan_folder(folder_path)
        return jsonify({'files': files})
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return jsonify({'error': str(e)}), 500


@files_bp.route('/load-path', methods=['POST'])
def load_path():
    """POST /api/files/load-path"""
    data = request.get_json()
    file_path = data.get('file_path', '')
    
    if not file_path:
        return jsonify({'error': 'File path required'}), 400
    
    try:
        result = file_service.load_by_path(file_path)
        return jsonify(result.to_dict())
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Load error: {e}")
        return jsonify({'error': str(e)}), 500
