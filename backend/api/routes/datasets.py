"""
Dataset routes
"""
from flask import Blueprint, jsonify
from backend.core.logger import get_logger
from backend.services.file_service import file_service

logger = get_logger(__name__)
datasets_bp = Blueprint('datasets', __name__)


@datasets_bp.route('/<dataset_hash>/preview', methods=['GET'])
def get_preview(dataset_hash):
    """GET /api/datasets/<hash>/preview"""
    try:
        df = file_service.load_dataframe(dataset_hash)

        columns = df.columns.tolist()
        dtypes = {col: str(df[col].dtype) for col in columns}
        sample = df.head(10).to_dict("records")
        missing = {col: int(df[col].isnull().sum()) for col in columns}

        return jsonify({
            "columns": columns,
            "dtypes": dtypes,
            "sample": sample,
            "shape": [int(df.shape[0]), int(df.shape[1])],
            "missing": missing,
        })
        
    except Exception as e:
        logger.error(f"Preview error: {e}")
        return jsonify({'error': str(e)}), 500
