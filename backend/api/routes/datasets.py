"""
Dataset routes
"""
import math
import numpy as np
from flask import Blueprint, jsonify
from backend.core.logger import get_logger
from backend.services.file_service import file_service

logger = get_logger(__name__)
datasets_bp = Blueprint('datasets', __name__)


def sanitize_value(val):
    """Convert NaN/Infinity to None for JSON serialization"""
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    if isinstance(val, (np.floating,)):
        fval = float(val)
        if math.isnan(fval) or math.isinf(fval):
            return None
        return fval
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    return val


def sanitize_record(record):
    """Sanitize all values in a record dict"""
    return {k: sanitize_value(v) for k, v in record.items()}


@datasets_bp.route('/<dataset_hash>/preview', methods=['GET'])
def get_preview(dataset_hash):
    """GET /api/datasets/<hash>/preview"""
    try:
        df = file_service.load_dataframe(dataset_hash)

        columns = df.columns.tolist()
        dtypes = {col: str(df[col].dtype) for col in columns}
        sample = [sanitize_record(record) for record in df.head(10).to_dict("records")]
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
