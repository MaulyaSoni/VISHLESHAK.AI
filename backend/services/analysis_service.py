"""
Analysis service - wraps the data agent
"""
import json
import queue
import threading
import uuid
from typing import Dict, Any, Optional, Callable
from backend.models.analysis import AnalysisRequest, AnalysisStatus
from backend.core.logger import get_logger

logger = get_logger(__name__)


class AnalysisService:
    """Analysis service"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._callbacks: Dict[str, Callable] = {}
    
    def start_analysis(
        self, 
        request: AnalysisRequest,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Start analysis and return session ID
        """
        session_id = str(uuid.uuid4())
        
        # Create session queue for SSE
        session_queue = queue.Queue()
        
        self._sessions[session_id] = {
            'request': request,
            'status': AnalysisStatus.RUNNING,
            'queue': session_queue,
            'result': None,
            'error': None
        }
        
        # Start analysis in background thread
        thread = threading.Thread(
            target=self._run_analysis,
            args=(session_id, request, progress_callback)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Analysis started: {session_id}")
        return session_id
    
    def _run_analysis(
        self, 
        session_id: str, 
        request: AnalysisRequest,
        progress_callback: Optional[Callable] = None
    ):
        """Run analysis in background"""
        session = self._sessions[session_id]
        
        try:
            # Import data agent here to avoid startup overhead
            try:
                from backend.scripts.data_agent_3 import run_agent
                from backend.services.file_service import file_service
                
                # Load dataset and build instruction
                df = file_service.load_dataframe(request.dataset_hash)
                if df is None:
                    raise ValueError(f"Dataset not found: {request.dataset_hash}")
                
                instruction = f"Analyze this dataset: {request.query}"
                
                # Run agent
                result = run_agent(instruction, force_task_type=request.mode)
                
                session['status'] = AnalysisStatus.DONE
                session['result'] = result
                
                # Send completion event
                session['queue'].put({
                    'type': 'done',
                    'final_response': result.get('executive_summary', 'Analysis complete'),
                    'pdf_path': result.get('pdf_path')
                })
                
                logger.info(f"Analysis completed: {session_id}")
                
            except Exception as e:
                logger.error(f"Agent error: {e}")
                session['status'] = AnalysisStatus.ERROR
                session['error'] = str(e)
                session['queue'].put({
                    'type': 'error',
                    'message': str(e)
                })
        
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            session['status'] = AnalysisStatus.ERROR
            session['error'] = str(e)
            session['queue'].put({
                'type': 'error',
                'message': str(e)
            })
    
    def get_session_queue(self, session_id: str) -> Optional[queue.Queue]:
        """Get session queue for SSE streaming"""
        session = self._sessions.get(session_id)
        if session:
            return session.get('queue')
        return None
    
    def get_session_status(self, session_id: str) -> Optional[AnalysisStatus]:
        """Get session status"""
        session = self._sessions.get(session_id)
        if session:
            return session.get('status')
        return None
    
    def get_session_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session result"""
        session = self._sessions.get(session_id)
        if session:
            return session.get('result')
        return None


# Singleton instance
analysis_service = AnalysisService()
