"""
Chat routes
"""
import json
import queue
import threading
from flask import Blueprint, request, jsonify, Response, stream_with_context
from backend.core.logger import get_logger
from backend.services.file_service import file_service
from database.chat_repository import ChatRepository

logger = get_logger(__name__)
chat_bp = Blueprint('chat', __name__)
chat_repo = ChatRepository()


@chat_bp.route('', methods=['POST'])
def chat():
    """POST /api/chat - SSE streaming chat"""
    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('session_id', '')
    dataset_hash = data.get('dataset_hash', '')
    conv_id = None
    try:
        if session_id and str(session_id).isdigit():
            conv_id = int(session_id)
    except Exception:
        conv_id = None
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    def generate():
        """Generate SSE stream"""
        try:
            # Save the user message to DB (best-effort) if session_id is a conversation id.
            if conv_id is not None:
                try:
                    chat_repo.save_message(
                        conversation_id=conv_id,
                        role="human",
                        content=message,
                        metadata={"dataset_hash": dataset_hash} if dataset_hash else None,
                    )
                except Exception as e:
                    logger.warning(f"Failed saving user message: {e}")

            # Load dataset if provided (optional for chat)
            df = None
            if dataset_hash:
                try:
                    df = file_service.load_dataframe(dataset_hash)
                except Exception as e:
                    logger.warning(f"Could not load dataset {dataset_hash}: {e}")

            # If no dataset, provide a helpful response but still allow chat
            if df is None or df.empty:
                response_text = (
                    "I'm Vishleshak AI, your data analysis assistant.\n\n"
                    "I can help you analyze data, find patterns, and generate insights.\n\n"
                    "⚠️ **No dataset loaded.** Upload a CSV or Excel file first, then ask me questions about your data!"
                )
                if conv_id is not None:
                    try:
                        chat_repo.save_message(
                            conversation_id=conv_id,
                            role="ai",
                            content=response_text,
                            metadata={"warning": "no_dataset"},
                        )
                    except Exception:
                        pass
                yield f"data: {json.dumps({'chunk': response_text})}\n\n"
                yield f"data: {json.dumps({'done': True, 'response': response_text})}\n\n"
                return

            # Try full chain; fall back to a clear error if optional deps are missing.
            try:
                from chatbot.qa_chain import EnhancedQAChain
                qa_chain = EnhancedQAChain(df, session_id=session_id or "default")
            except Exception as e:
                response_text = (
                    "Chat engine isn't fully available on this server.\n\n"
                    f"Reason: {e}\n\n"
                    "Fix: install missing Python deps (e.g. `sentence-transformers`) and set `GROQ_API_KEY`."
                )
                if conv_id is not None:
                    try:
                        chat_repo.save_message(
                            conversation_id=conv_id,
                            role="ai",
                            content=response_text,
                            metadata={"error": str(e)},
                        )
                    except Exception:
                        pass
                yield f"data: {json.dumps({'done': True, 'response': response_text})}\n\n"
                return

            # Stream using the chain's callback by running in a thread and draining a queue.
            q: "queue.Queue[str | None]" = queue.Queue()

            def _run():
                try:
                    qa_chain.ask(
                        message,
                        use_rag=True,
                        return_dict=False,
                        stream_callback=lambda t: q.put(t),
                    )
                except Exception as e:
                    q.put(f"\n\n[Error: {e}]")
                finally:
                    q.put(None)  # sentinel

            t = threading.Thread(target=_run, daemon=True)
            t.start()

            full = []
            while True:
                item = q.get()
                if item is None:
                    break
                full.append(item)
                yield f"data: {json.dumps({'chunk': item})}\n\n"

            response_text = "".join(full).strip()

            # Save assistant message to DB (best-effort)
            if conv_id is not None:
                try:
                    chat_repo.save_message(
                        conversation_id=conv_id,
                        role="ai",
                        content=response_text,
                        metadata=None,
                    )
                except Exception as e:
                    logger.warning(f"Failed saving assistant message: {e}")

            yield f"data: {json.dumps({'done': True, 'response': response_text})}\n\n"
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"data: {json.dumps({'done': True, 'response': f'Chat failed: {e}'})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )
