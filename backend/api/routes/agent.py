"""
Data Agent routes
"""
import json
import threading
import os
from flask import Blueprint, request, jsonify, g
from backend.core.logger import get_logger
from config import settings
from database.analysis_repository import analysis_repository
from backend.services.file_service import file_service

logger = get_logger(__name__)
agent_bp = Blueprint('agent', __name__)

# In-memory storage for agent progress (use Redis in production)
agent_progress = {}
agent_threads = {}


def get_current_user_id():
    """Get current user ID from JWT token or default to 1"""
    return getattr(g, 'user_id', 1)


@agent_bp.route('/run', methods=['POST'])
def run_agent():
    """POST /api/agent/run"""
    data = request.get_json()
    instruction = data.get('instruction', '')
    mode = data.get('mode', 'analysis_ml')
    dataset_hash = data.get('dataset_hash', '')
    
    if not instruction:
        return jsonify({'error': 'Instruction required'}), 400
    
    session_id = request.headers.get('X-Session-ID', 'default')
    user_id = get_current_user_id()
    
    # Initialize progress
    agent_progress[session_id] = {
        'status': 'running',
        'steps': [],
        'progress': 0,
        'report': None,
        'error': None,
        'user_id': user_id,
        'report_id': None
    }
    
    # Create database entry for this analysis
    try:
        report = analysis_repository.create_report(
            user_id=user_id,
            session_id=session_id,
            title=instruction[:100],
            instruction=instruction,
            mode=mode,
            status='running'
        )
        agent_progress[session_id]['report_id'] = report.id
    except Exception as e:
        logger.error(f"Failed to create analysis report: {e}")
    
    # Get report_id before starting thread
    report_id = agent_progress[session_id].get('report_id')
    
    # Start agent in background thread (real agent implementation)
    def run_agent_thread():
        try:
            from backend.scripts import data_agent_3

            # Provide agent a place to scan if it needs local files.
            # If dataset_hash is provided, we enrich the instruction with the file path
            # so the agent loads the right dataset deterministically.
            if dataset_hash:
                ds = file_service.get_dataset(dataset_hash)
                if ds and ds.filepath:
                    instruction_effective = f"{instruction}\n\nDATASET_FILE: {ds.filepath}"
                else:
                    instruction_effective = instruction
            else:
                instruction_effective = instruction

            # Reset progress
            agent_progress[session_id]["steps"] = []
            agent_progress[session_id]["progress"] = 0

            def _on_progress(evt: dict):
                # evt: {"step": "...", "status": "done|..."}
                step_text = str(evt.get("step", "")).strip()
                if not step_text:
                    return
                agent_progress[session_id]["steps"].append({
                    "step": step_text,
                    "status": evt.get("status", "done"),
                })
                # Best-effort progress estimate based on steps list (agent has variable length)
                agent_progress[session_id]["progress"] = min(95, len(agent_progress[session_id]["steps"]) * 5)

            data_agent_3.set_progress_callback(_on_progress)

            report_data = data_agent_3.run_agent(instruction_effective, force_task_type=mode)
            agent_progress[session_id]["progress"] = 100
            
            agent_progress[session_id]['report'] = report_data
            agent_progress[session_id]['status'] = 'done'
            
            # Update database with completed report
            if report_id:
                try:
                    analysis_repository.update_report(
                        report_id=report_id,
                        report_data=report_data,
                        status='completed'
                    )
                except Exception as e:
                    logger.error(f"Failed to update analysis report: {e}")
            
        except Exception as e:
            logger.error(f"Agent error: {e}")
            agent_progress[session_id]['status'] = 'error'
            agent_progress[session_id]['error'] = str(e)
    
    thread = threading.Thread(target=run_agent_thread, daemon=True)
    thread.start()
    agent_threads[session_id] = thread
    
    return jsonify({
        'session_id': session_id,
        'status': 'running'
    })


@agent_bp.route('/progress', methods=['GET'])
def get_progress():
    """GET /api/agent/progress"""
    session_id = request.headers.get('X-Session-ID', 'default')
    progress = agent_progress.get(session_id, {
        'status': 'idle',
        'steps': [],
        'progress': 0
    })
    return jsonify(progress)


@agent_bp.route('/stop', methods=['POST'])
def stop_agent():
    """POST /api/agent/stop"""
    session_id = request.headers.get('X-Session-ID', 'default')
    if session_id in agent_progress:
        agent_progress[session_id]['status'] = 'stopped'
        try:
            from backend.scripts.data_agent_3 import cancel_agent
            cancel_agent()
        except Exception:
            pass
    return jsonify({'status': 'stopped'})


@agent_bp.route('/notebook/<filename>', methods=['GET'])
def download_notebook(filename):
    """GET /api/agent/notebook/<filename> - Download notebook file"""
    try:
        notebook_dir = os.path.join(settings.UPLOAD_FOLDER, '..', 'notebooks')
        file_path = os.path.join(notebook_dir, filename)
        
        # Security check: ensure file is within notebooks directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(notebook_dir)):
            return jsonify({'error': 'Invalid filename'}), 400
        
        if os.path.exists(file_path):
            from flask import send_file
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'Notebook not found'}), 404
            
    except Exception as e:
        logger.error(f"Notebook download error: {e}")
        return jsonify({'error': str(e)}), 500
