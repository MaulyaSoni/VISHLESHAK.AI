"""
File Routes - Handles file uploads, scanning, and loading
"""
import os
import uuid
from flask import Blueprint, request, jsonify

file_bp = Blueprint('files', __name__)

UPLOAD_FOLDER = 'data/uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """POST /api/files/upload - Upload a dataset file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed: {ALLOWED_EXTENSIONS}'}), 400
    
    try:
        # Ensure upload folder exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file with unique name
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Get file stats
        file_size = os.path.getsize(filepath)
        
        # Try to load and get metadata
        try:
            import pandas as pd
            df = pd.read_csv(filepath) if filepath.endswith('.csv') else pd.read_excel(filepath)
            rows, cols = df.shape
            
            # Generate dataset hash
            dataset_hash = uuid.uuid4().hex[:16]
            
            return jsonify({
                'success': True,
                'dataset_hash': dataset_hash,
                'filename': file.filename,
                'stored_filename': filename,
                'filepath': filepath,
                'rows': rows,
                'cols': cols,
                'size_bytes': file_size,
                'meta': {
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.astype(str).to_dict()
                }
            })
        except Exception as e:
            # Return basic info if parsing fails
            return jsonify({
                'success': True,
                'dataset_hash': uuid.uuid4().hex[:16],
                'filename': file.filename,
                'stored_filename': filename,
                'filepath': filepath,
                'size_bytes': file_size,
                'warning': f'File saved but could not parse: {str(e)}'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@file_bp.route('/scan', methods=['POST'])
def scan_folder():
    """POST /api/files/scan - Scan folder for data files"""
    data = request.get_json() or {}
    folder_path = data.get('folder_path', '.')
    
    try:
        files = []
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path) and allowed_file(item):
                stat = os.stat(item_path)
                files.append({
                    'name': item,
                    'path': item_path,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': stat.st_mtime
                })
        
        return jsonify({
            'success': True,
            'folder': folder_path,
            'files': files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@file_bp.route('/load-path', methods=['POST'])
def load_path():
    """POST /api/files/load-path - Load file from absolute path"""
    data = request.get_json() or {}
    file_path = data.get('file_path', '')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    if not allowed_file(file_path):
        return jsonify({'error': f'Invalid file type. Allowed: {ALLOWED_EXTENSIONS}'}), 400
    
    try:
        import pandas as pd
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        rows, cols = df.shape
        
        dataset_hash = uuid.uuid4().hex[:16]
        
        return jsonify({
            'success': True,
            'dataset_hash': dataset_hash,
            'filename': os.path.basename(file_path),
            'filepath': file_path,
            'rows': rows,
            'cols': cols,
            'meta': {
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.astype(str).to_dict()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
