"""
Report Routes - Handles report listing and downloads
"""
import os
from flask import Blueprint, jsonify, send_file
from flask_login import login_required, current_user

report_bp = Blueprint('reports', __name__)

REPORTS_FOLDER = 'storage/exports'


@report_bp.route('/list', methods=['GET'])
@login_required
def list_reports():
    """GET /api/reports/list - List all reports for user"""
    try:
        user_id = str(current_user.id)
        user_reports_folder = os.path.join(REPORTS_FOLDER, user_id)
        
        if not os.path.exists(user_reports_folder):
            return jsonify([])
        
        reports = []
        for filename in os.listdir(user_reports_folder):
            filepath = os.path.join(user_reports_folder, filename)
            if os.path.isfile(filepath) and filename.endswith('.pdf'):
                stat = os.stat(filepath)
                reports.append({
                    'filename': filename,
                    'mode': 'analysis',  # Could be extracted from filename or metadata
                    'domain': current_user.domain,
                    'created_at': stat.st_mtime,
                    'size_kb': round(stat.st_size / 1024, 2)
                })
        
        # Sort by creation time, newest first
        reports.sort(key=lambda x: x['created_at'], reverse=True)
        return jsonify(reports)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/download/<filename>', methods=['GET'])
@login_required
def download_report(filename: str):
    """GET /api/reports/download/:id - Download a report PDF"""
    try:
        user_id = str(current_user.id)
        filepath = os.path.join(REPORTS_FOLDER, user_id, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Report not found'}), 404
        
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
