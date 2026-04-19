"""
Analysis Routes - Wraps supervisor_graph and data_agent for real-time streaming
"""
import json
import queue
import threading
import time
from flask import Blueprint, request, jsonify, Response, stream_with_context

analysis_bp = Blueprint('analysis', __name__)

# Session-based queues for SSE streaming
session_queues = {}


def get_session_queue(session_id):
    """Get or create a queue for a session"""
    if session_id not in session_queues:
        session_queues[session_id] = queue.Queue()
    return session_queues[session_id]


def stream_callback(session_id, event_type, data):
    """Callback to send events to the session queue"""
    if session_id in session_queues:
        event = {'type': event_type, **data}
        session_queues[session_id].put(event)


@analysis_bp.route('/run', methods=['POST'])
def run_analysis():
    """POST /api/analysis/run - Start analysis in background thread"""
    data = request.get_json() or {}
    
    query = data.get('query', '')
    dataset_hash = data.get('dataset_hash', '')
    domain = data.get('domain', 'general')
    pdf_trigger = data.get('pdf_trigger', False)
    session_id = data.get('session_id', '')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    if not session_id:
        return jsonify({'error': 'Session ID is required'}), 400
    
    try:
        # Initialize queue for this session
        q = get_session_queue(session_id)
        
        # Clear any old events
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                break
        
        # Start analysis in background thread
        def run_analysis_thread():
            try:
                # Import here to avoid circular imports
                try:
                    from agentic_core.supervisor_graph import run_supervisor
                    SUPERVISOR_AVAILABLE = True
                except ImportError:
                    SUPERVISOR_AVAILABLE = False
                
                if SUPERVISOR_AVAILABLE:
                    # Use supervisor graph
                    stream_callback(session_id, 'trace', {
                        'agent': 'supervisor',
                        'action': 'start',
                        'output': 'Starting analysis...'
                    })
                    
                    result = run_supervisor(query, dataset_hash)
                    
                    stream_callback(session_id, 'done', {
                        'final_response': result.get('final_response', 'Analysis complete'),
                        'pdf_path': result.get('pdf_path', ''),
                        'charts': result.get('charts', []),
                        'insights': result.get('insights', {})
                    })
                else:
                    # Fallback: use data_agent_3
                    from data_agent_3 import run_agent
                    
                    stream_callback(session_id, 'trace', {
                        'agent': 'data_agent',
                        'action': 'start',
                        'output': 'Starting data analysis...'
                    })
                    
                    # Run agent with progress tracking
                    report = run_agent(query)
                    
                    stream_callback(session_id, 'done', {
                        'final_response': report.get('insights', {}).get('executive_summary', 'Analysis complete'),
                        'pdf_path': '',
                        'charts': report.get('charts', []),
                        'insights': report.get('insights', {}),
                        'report': report
                    })
                    
            except Exception as e:
                stream_callback(session_id, 'error', {'message': str(e)})
        
        thread = threading.Thread(target=run_analysis_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': 'started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/stream', methods=['GET'])
def stream_analysis():
    """GET /api/analysis/stream - SSE endpoint for real-time updates"""
    session_id = request.args.get('session_id', '')
    
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 400
    
    def generate():
        q = get_session_queue(session_id)
        
        while True:
            try:
                # Wait for event with timeout
                event = q.get(timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
                
                # Stop if done or error
                if event.get('type') in ('done', 'error'):
                    break
                    
            except queue.Empty:
                # Send keepalive
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                continue
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
        
        # Cleanup
        if session_id in session_queues:
            del session_queues[session_id]
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@analysis_bp.route('/status/<session_id>', methods=['GET'])
def get_status(session_id):
    """GET /api/analysis/status/<session_id> - Check analysis status"""
    # This is a simple polling endpoint as fallback
    return jsonify({
        'session_id': session_id,
        'status': 'running' if session_id in session_queues else 'unknown'
    })
