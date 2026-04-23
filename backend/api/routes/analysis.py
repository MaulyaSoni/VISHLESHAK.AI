"""
Analysis routes
"""
import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from backend.services.analysis_service import analysis_service
from backend.models.analysis import AnalysisRequest
from backend.core.logger import get_logger

logger = get_logger(__name__)
analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/generate-charts', methods=['POST'])
def generate_charts():
    """POST /api/analysis/generate-charts - Generate visualization charts for dataset"""
    data = request.get_json()
    dataset_hash = data.get('dataset_hash', '')
    
    if not dataset_hash:
        return jsonify({"error": "dataset_hash required"}), 400
    
    try:
        # Load dataset
        from backend.services.file_service import file_service
        from backend.app_modules.utils.dashboard_visualizer import DashboardVisualizer
        import plotly.io as pio
        
        logger.info(f"Generating charts for dataset: {dataset_hash}")
        df = file_service.load_dataframe(dataset_hash)
        if df is None:
            return jsonify({"error": "Dataset not found"}), 404
        
        # Generate charts using DashboardVisualizer
        visualizer = DashboardVisualizer(df)
        charts = visualizer.create_overview_dashboard()
        
        logger.info(f"Generated {len(charts)} charts")
        
        # Convert Plotly figures to JSON for frontend
        charts_json = []
        for title, fig in charts:
            chart_json = pio.to_json(fig)
            charts_json.append({
                'title': title,
                'plotly_json': json.loads(chart_json)
            })
        
        logger.info(f"Returning {len(charts_json)} charts to frontend")
        return jsonify({
            'charts': charts_json,
            'count': len(charts_json)
        })
        
    except Exception as e:
        logger.error(f"Chart generation error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def convert_to_serializable(obj):
    """Convert numpy types and other non-JSON-serializable types to Python native types"""
    import numpy as np
    import pandas as pd
    import math
    
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        val = float(obj)
        # Handle NaN and Infinity
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    elif isinstance(obj, float):
        # Handle Python native float NaN/Infinity
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, np.ndarray):
        return [convert_to_serializable(item) for item in obj.tolist()]
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif pd.isna(obj) if hasattr(pd, 'isna') else obj is None:
        return None
    else:
        return obj


@analysis_bp.route('/run', methods=['POST'])
def run_analysis():
    """POST /api/analysis/run"""
    data = request.get_json()
    
    try:
        request_obj = AnalysisRequest(
            query=data.get('query', ''),
            dataset_hash=data.get('dataset_hash', ''),
            domain=data.get('domain', 'general'),
            mode=data.get('mode', 'analysis_only')
        )
        
        session_id = analysis_service.start_analysis(request_obj)
        
        return jsonify({
            'session_id': session_id,
            'status': 'running'
        })
    
    except Exception as e:
        logger.error(f"Analysis start error: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/stream', methods=['GET'])
def stream_analysis():
    """GET /api/analysis/stream - SSE endpoint"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'session_id required'}), 400
    
    def generate():
        import queue
        
        q = analysis_service.get_session_queue(session_id)
        if not q:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'})}\n\n"
            return
        
        while True:
            try:
                event = q.get(timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
                
                if event.get('type') in ('done', 'error'):
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@analysis_bp.route('', methods=['POST'])
def analyze():
    """POST /api/analyze - Simple analysis endpoint"""
    data = request.get_json()
    dataset_hash = data.get('dataset_hash', '')
    use_agent_mode = data.get('use_agent_mode', False)
    domain = data.get('domain', 'general')
    
    try:
        if not dataset_hash:
            return jsonify({"error": "dataset_hash required"}), 400

        # Load real dataset and run the same core v1 analysis used by Streamlit.
        from backend.services.file_service import file_service
        from analyzers.insight_generator import InsightGenerator

        df = file_service.load_dataframe(dataset_hash)
        insights = InsightGenerator(df).generate_comprehensive_insights()

        basic_info = insights.get("statistical_analysis", {}).get("basic_info", {})
        profile = {
            "rows": int(basic_info.get("total_rows", len(df))),
            "columns": int(basic_info.get("total_columns", len(df.columns))),
            "numeric_count": int(basic_info.get("numeric_columns", len(df.select_dtypes(include=["number"]).columns))),
            "categorical_count": int(basic_info.get("categorical_columns", len(df.select_dtypes(include=["object", "category"]).columns))),
        }

        # Convert all values to JSON-serializable types
        response_data = {
            "analysis": {
                "executive_summary": insights.get("executive_summary"),
                "ai_insights": insights.get("ai_insights"),
                "recommendations": insights.get("recommendations", []),
                "statistics": convert_to_serializable(insights.get("statistical_analysis", {})),
                "patterns": convert_to_serializable(insights.get("pattern_analysis", {})),
                "profile": convert_to_serializable(profile),
                "domain": domain,
                "is_v2": bool(use_agent_mode),
            },
            "charts": [],
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'error': str(e)}), 500
