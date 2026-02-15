"""
Enhanced Q&A Chain for FINBOT v4
Integrates RAG, tools, memory, and Phase 3 quality learning
"""

import pandas as pd
from typing import Dict, Any, Optional, List, Union
from langchain_core.output_parsers import StrOutputParser
from core.llm import get_chat_llm
from core.memory import ChatMemoryManager
from chatbot.context_manager import ContextManager
from chatbot.prompt_templates import QA_WITH_RAG_PROMPT, QA_SIMPLE_PROMPT
from chatbot.improvement_loop import get_improvement_loop
from chatbot.feedback_collector import FeedbackType
from tools.tool_registry import get_tool_registry
import logging

logger = logging.getLogger(__name__)


class EnhancedQAChain:
    """
    Enhanced Q&A chain with RAG and tool integration
    
    Features:
    - RAG-augmented responses
    - Tool integration
    - Conversation memory
    - Context-aware answers
    
    Usage:
        qa_chain = EnhancedQAChain(df, session_id="user123")
        response = qa_chain.ask("What's the average dropout risk?")
    """
    
    def __init__(self, df: pd.DataFrame, session_id: str = "default"):
        """
        Initialize enhanced Q&A chain
        
        Args:
            df: DataFrame with data
            session_id: Unique session identifier
        """
        self.df = df
        self.session_id = session_id
        self.llm = get_chat_llm()
        self.memory = ChatMemoryManager(session_id)
        self.context_manager = ContextManager()
        self.tool_registry = get_tool_registry()
        self.improvement_loop = get_improvement_loop()  # Phase 3 integration
        
        # Track message IDs for feedback correlation
        self._message_counter = 0
        self._last_message_id = None
        
        # Initialize data context
        self._initialize_data_context()
        
        logger.info(f"✅ Enhanced Q&A chain initialized for session: {session_id} (with Phase 3 Quality Learning)")
    
    def _initialize_data_context(self):
        """Save data context to memory"""
        summary = self._create_data_summary()
        self.memory.save_data_context(
            data_summary=summary,
            columns=list(self.df.columns)
        )
    
    def _create_data_summary(self) -> str:
        """Create comprehensive data summary"""
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"Dataset: {self.df.shape[0]} rows × {self.df.shape[1]} columns")
        summary_parts.append(f"Columns: {', '.join(self.df.columns.tolist())}")
        
        # Numeric summaries
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_parts.append("\nNumeric Columns:")
            for col in numeric_cols[:5]:
                summary_parts.append(
                    f"  {col}: mean={self.df[col].mean():.2f}, "
                    f"range=[{self.df[col].min():.2f}, {self.df[col].max():.2f}]"
                )
        
        # Categorical info
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            summary_parts.append("\nCategorical Columns:")
            for col in categorical_cols[:5]:
                unique = self.df[col].nunique()
                summary_parts.append(f"  {col}: {unique} unique values")
        
        return "\n".join(summary_parts)
    
    def ask(self, question: str, use_rag: bool = True, return_dict: bool = False) -> Union[str, Dict[str, Any]]:
        """
        Ask a question about the data
        
        Args:
            question: User question
            use_rag: Whether to use RAG for context
            return_dict: If True, returns dict with quality info; if False, returns just the formatted response
            
        Returns:
            If return_dict=False: Formatted response string (default for backward compatibility)
            If return_dict=True: Dict with formatted_response, quality_score, message_id, etc.
        """
        logger.info(f"Question: {question}")
        
        # Increment message ID
        self._message_counter += 1
        message_id = self._message_counter
        self._last_message_id = message_id
        
        # Save question to memory
        self.memory.add_message(self.session_id, "human", question)
        
        # Get data context
        data_context = self._get_data_context()
        
        # Determine if we should use RAG
        should_use_rag = use_rag and self.context_manager.should_use_rag(question)
        
        # Get RAG context if needed
        rag_context = ""
        if should_use_rag:
            context_result = self.context_manager.get_context_for_query(question)
            if context_result["has_context"]:
                rag_context = context_result["formatted_context"]
                logger.info(f"Using RAG context from {len(context_result['sources'])} sources")
        
        # Get chat history
        history = self.memory.get_memory_variables()["chat_history"]
        
        # Select prompt template
        if rag_context:
            prompt = QA_WITH_RAG_PROMPT
            prompt_vars = {
                "data_context": data_context,
                "rag_context": rag_context,
                "chat_history": history,
                "question": question
            }
        else:
            prompt = QA_SIMPLE_PROMPT
            prompt_vars = {
                "data_context": data_context,
                "chat_history": history,
                "question": question
            }
        
        # Create and execute chain
        try:
            chain = prompt | self.llm | StrOutputParser()
            raw_response = chain.invoke(prompt_vars)
            
            # ===== PHASE 3 INTEGRATION: Process through improvement loop =====
            improvement_result = self.improvement_loop.process_response(
                question=question,
                response=raw_response,
                user_id=self.session_id,  # Use session_id as user_id
                session_id=self.session_id,
                message_id=message_id,
                data_context=data_context,
                question_type="analytical"  # Can be enhanced to auto-detect
            )
            
            formatted_response = improvement_result["formatted_response"]
            quality_score = improvement_result["quality_score"]
            # ==================================================================
            
            # Save formatted response to memory
            self.memory.add_message(self.session_id, "ai", formatted_response)
            
            # Save to RAG if significant
            if should_use_rag:
                self.context_manager.save_interaction_to_rag(
                    query=question,
                    response=formatted_response,
                    metadata={
                        "session_id": self.session_id,
                        "dataset_shape": str(self.df.shape),
                        "quality_score": quality_score.overall_score,
                        "quality_grade": quality_score.get_grade()
                    }
                )
            
            logger.info(f"Response generated (Quality: {quality_score.overall_score:.1f}/100, Grade: {quality_score.get_grade()})")
            
            # Return based on return_dict flag
            if return_dict:
                return improvement_result
            else:
                return formatted_response  # Backward compatibility
        
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            self.memory.add_message(self.session_id, "ai", error_msg)
            
            if return_dict:
                return {
                    "formatted_response": error_msg,
                    "quality_score": None,
                    "message_id": message_id,
                    "error": True
                }
            else:
                return error_msg
    
    def provide_feedback(
        self, 
        feedback_type: str, 
        feedback_value: Optional[int] = None,
        message_id: Optional[int] = None,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Provide feedback on the last (or specified) response
        
        Phase 3 Integration: Feedback triggers preference learning
        
        Args:
            feedback_type: Type of feedback - "thumbs_up", "thumbs_down", "rating", "comment"
            feedback_value: Numeric value (1 for thumbs_up, -1 for thumbs_down, 1-5 for rating)
            message_id: Specific message ID to provide feedback for (defaults to last message)
            comment: Optional text comment
            
        Returns:
            Dict with feedback confirmation and learning status
            
        Examples:
            qa_chain.provide_feedback("thumbs_up")
            qa_chain.provide_feedback("rating", feedback_value=4)
            qa_chain.provide_feedback("comment", comment="Great analysis!")
        """
        # Use last message if not specified
        target_message_id = message_id or self._last_message_id
        
        if target_message_id is None:
            return {
                "success": False,
                "error": "No message to provide feedback for"
            }
        
        # Convert feedback_type string to enum
        try:
            if feedback_type == "thumbs_up":
                fb_type = FeedbackType.THUMBS_UP
                fb_value = 1 if feedback_value is None else feedback_value
            elif feedback_type == "thumbs_down":
                fb_type = FeedbackType.THUMBS_DOWN
                fb_value = -1 if feedback_value is None else feedback_value
            elif feedback_type == "rating":
                fb_type = FeedbackType.RATING
                fb_value = feedback_value or 3
            elif feedback_type == "comment":
                fb_type = FeedbackType.COMMENT
                fb_value = 0
            else:
                return {
                    "success": False,
                    "error": f"Unknown feedback type: {feedback_type}"
                }
        except Exception as e:
            logger.error(f"Error processing feedback type: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
        # Get the question and response from memory
        chat_history = self.memory.get_chat_history()
        
        # Find the corresponding Q&A pair
        # Messages are stored alternately (human, ai, human, ai...)
        # For message_id N, we need the N-th exchange
        if len(chat_history) >= target_message_id * 2:
            question_text = chat_history[target_message_id * 2 - 2]["content"]
            response_text = chat_history[target_message_id * 2 - 1]["content"]
        else:
            logger.warning(f"Could not find message {target_message_id} in history")
            question_text = "Unknown"
            response_text = "Unknown"
        
        # Trigger Phase 3 feedback handling
        try:
            self.improvement_loop.handle_feedback(
                user_id=self.session_id,
                session_id=self.session_id,
                message_id=target_message_id,
                feedback_type=fb_type,
                feedback_value=fb_value,
                comment=comment,
                question_text=question_text,
                response_text=response_text,
                response_metadata={
                    "response_length": len(response_text),
                    "question_length": len(question_text)
                }
            )
            
            logger.info(f"Feedback processed: {feedback_type} for message {target_message_id}")
            
            return {
                "success": True,
                "feedback_type": feedback_type,
                "message_id": target_message_id,
                "learning_triggered": True
            }
        
        except Exception as e:
            logger.error(f"Error handling feedback: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """
        Get quality and improvement metrics
        
        Returns:
            Dict with quality trends and learning progress
        """
        return self.improvement_loop.get_improvement_metrics()
    
    def ask_with_tools(self, question: str) -> Dict[str, Any]:
        """
        Ask a question with tool support
        
        Args:
            question: User question
            
        Returns:
            Dict with answer and tool results
        """
        # Identify if tools are needed
        tools_needed = self._identify_needed_tools(question)
        
        if not tools_needed:
            # No tools needed, use regular ask
            return {
                "answer": self.ask(question),
                "tools_used": []
            }
        
        # Execute with tools
        tool_results = []
        for tool_name in tools_needed:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                # Execute tool (simplified - in practice, need proper parameters)
                logger.info(f"Would execute tool: {tool_name}")
                tool_results.append({
                    "tool": tool_name,
                    "result": "Tool execution would happen here"
                })
        
        # Generate answer incorporating tool results
        answer = self.ask(question)
        
        return {
            "answer": answer,
            "tools_used": tool_results
        }
    
    def _identify_needed_tools(self, question: str) -> list:
        """Identify which tools might be needed"""
        tools = []
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["plot", "chart", "visualize", "graph"]):
            tools.append("chart_generator")
        
        if any(word in question_lower for word in ["filter", "sort", "transform"]):
            tools.append("data_transformer")
        
        if any(word in question_lower for word in ["calculate", "compute", "equation"]):
            tools.append("calculator")
        
        if any(word in question_lower for word in ["export", "save", "download"]):
            tools.append("export")
        
        return tools
    
    def _get_data_context(self) -> str:
        """Get current data context"""
        saved_context = self.memory.get_data_context()
        if saved_context:
            return saved_context["summary"]
        return self._create_data_summary()
    
    def get_chat_history(self) -> list:
        """Get chat history"""
        return self.memory.get_chat_history()
    
    def clear_history(self):
        """Clear chat history"""
        self.memory.clear_history()
        self._initialize_data_context()


class DataContextManager:
    """Manages Q&A contexts for multiple sessions"""
    
    def __init__(self):
        self.active_contexts: Dict[str, EnhancedQAChain] = {}
    
    def create_context(self, session_id: str, df: pd.DataFrame) -> EnhancedQAChain:
        """Create new Q&A context"""
        qa_chain = EnhancedQAChain(df, session_id)
        self.active_contexts[session_id] = qa_chain
        return qa_chain
    
    def get_context(self, session_id: str) -> Optional[EnhancedQAChain]:
        """Get existing context"""
        return self.active_contexts.get(session_id)
    
    def remove_context(self, session_id: str):
        """Remove context"""
        if session_id in self.active_contexts:
            del self.active_contexts[session_id]
