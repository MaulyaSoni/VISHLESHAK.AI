"""
Sequential Chain Manager for FINBOT v4
Orchestrates multi-step reasoning with memory integration
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from enum import Enum

from chatbot.question_decomposer import get_question_decomposer, QuestionDecomposer
from chatbot.cot_reasoner import get_cot_reasoner, ChainOfThoughtReasoner
from core.enhanced_memory import EnhancedMemoryManager
from config import chain_config

logger = logging.getLogger(__name__)


class ChainType(Enum):
    """Available chain types"""
    SIMPLE = "simple"
    SEQUENTIAL = "sequential"
    DECOMPOSITION = "decomposition"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    MEMORY_AUGMENTED = "memory_augmented"


class SequentialChainManager:
    """
    Main orchestrator for sequential reasoning chains
    
    Combines:
    - Question decomposition
    - Chain-of-thought reasoning
    - Memory integration
    - Multi-step execution
    
    Routing Logic:
    - Simple questions → Direct answer
    - Complex questions → Decompose + Sequential reasoning
    - Analytical questions → Chain-of-thought
    - Questions referencing history → Memory-augmented reasoning
    
    Usage:
        chain_manager = SequentialChainManager(memory_manager)
        result = chain_manager.execute(question, data_context)
    """
    
    def __init__(self, memory_manager: Optional[EnhancedMemoryManager] = None):
        """
        Initialize sequential chain manager
        
        Args:
            memory_manager: Enhanced memory manager instance
        """
        self.memory = memory_manager
        self.decomposer = get_question_decomposer()
        self.cot_reasoner = get_cot_reasoner(memory_manager)
        
        # Execution statistics
        self.stats = {
            "total_executions": 0,
            "by_chain_type": {},
            "avg_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        
        logger.info("✅ Sequential chain manager initialized")
    
    def execute(
        self,
        question: str,
        data_context: str,
        chain_type: Optional[ChainType] = None,
        chat_history: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Execute reasoning chain
        
        Args:
            question: User's question
            data_context: Available data context
            chain_type: Force specific chain type (auto-detected if None)
            chat_history: Conversation history
            
        Returns:
            Dict with answer and execution metadata
        """
        start_time = datetime.now()
        
        logger.info(f"🚀 Executing chain for: {question[:60]}...")
        
        # Auto-detect chain type if not specified
        if chain_type is None:
            chain_type = self._detect_chain_type(question)
        
        logger.info(f"Chain type: {chain_type.value}")
        
        # Route to appropriate chain
        try:
            if chain_type == ChainType.SIMPLE:
                result = self._execute_simple_chain(question, data_context)
            
            elif chain_type == ChainType.SEQUENTIAL:
                result = self._execute_sequential_chain(question, data_context, chat_history)
            
            elif chain_type == ChainType.DECOMPOSITION:
                result = self._execute_decomposition_chain(question, data_context, chat_history)
            
            elif chain_type == ChainType.CHAIN_OF_THOUGHT:
                result = self._execute_cot_chain(question, data_context, chat_history)
            
            elif chain_type == ChainType.MEMORY_AUGMENTED:
                result = self._execute_memory_augmented_chain(question, data_context, chat_history)
            
            else:
                # Fallback to simple
                logger.warning(f"Unknown chain type: {chain_type}, using simple")
                result = self._execute_simple_chain(question, data_context)
            
            # Add metadata
            execution_time = (datetime.now() - start_time).total_seconds()
            result["metadata"] = {
                "chain_type": chain_type.value,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update statistics
            self._update_stats(chain_type, execution_time)
            
            logger.info(f"✅ Chain execution complete in {execution_time:.2f}s")
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing chain: {e}", exc_info=True)
            
            # Fallback to simple chain
            if chain_config.FALLBACK_TO_SIMPLE and chain_type != ChainType.SIMPLE:
                logger.info("Falling back to simple chain...")
                return self._execute_simple_chain(question, data_context)
            
            raise
    
    def _detect_chain_type(self, question: str) -> ChainType:
        """
        Auto-detect appropriate chain type
        
        Args:
            question: User's question
            
        Returns:
            ChainType enum
        """
        question_lower = question.lower()
        
        # Check for memory-related keywords
        memory_keywords = [
            'previous', 'last time', 'before', 'earlier', 'we discussed',
            'remember', 'you said', 'compare to', 'difference from'
        ]
        if any(keyword in question_lower for keyword in memory_keywords):
            return ChainType.MEMORY_AUGMENTED
        
        # Check for analytical keywords (CoT appropriate)
        analytical_keywords = [
            'why', 'how', 'explain', 'analyze', 'reasoning',
            'cause', 'impact', 'effect', 'relationship', 'correlation'
        ]
        if any(keyword in question_lower for keyword in analytical_keywords):
            return ChainType.CHAIN_OF_THOUGHT
        
        # Check complexity for decomposition
        if self.decomposer._is_complex(question):
            return ChainType.DECOMPOSITION
        
        # Default to simple for straightforward questions
        return ChainType.SIMPLE
    
    # ========================================================================
    # CHAIN EXECUTION METHODS
    # ========================================================================
    
    def _execute_simple_chain(
        self,
        question: str,
        data_context: str
    ) -> Dict[str, Any]:
        """
        Execute simple direct chain (no decomposition, minimal reasoning)
        
        Best for: Simple factual questions, quick lookups
        """
        logger.debug("Executing simple chain...")
        
        # Direct answer without explicit reasoning
        from core.llm import get_chat_llm
        
        prompt = f"""Answer this question concisely based on the data.

DATA CONTEXT:
{data_context}

QUESTION: {question}

ANSWER:"""
        
        response = get_chat_llm().invoke(prompt)
        
        return {
            "answer": response.content,
            "reasoning_visible": False,
            "steps": []
        }
    
    def _execute_sequential_chain(
        self,
        question: str,
        data_context: str,
        chat_history: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Execute sequential chain (multi-step without decomposition)
        
        Best for: Questions requiring multiple operations in sequence
        """
        logger.debug("Executing sequential chain...")
        
        steps = []
        
        # Step 1: Understand
        understanding = self._understand_question(question)
        steps.append({"name": "understand", "result": understanding})
        
        # Step 2: Retrieve context
        if self.memory:
            context = self.memory.retrieve_context(question, strategy="conservative")
            context_formatted = self.memory.format_context_for_prompt(context)
            steps.append({"name": "retrieve", "result": "Context retrieved"})
        else:
            context_formatted = ""
        
        # Step 3: Reason
        reasoning_prompt = f"""Based on the understanding and context, answer the question.

UNDERSTANDING:
{understanding}

CONTEXT:
{context_formatted}

DATA:
{data_context}

QUESTION: {question}

Provide a clear, direct answer:"""
        
        from core.llm import get_chat_llm
        response = get_chat_llm().invoke(reasoning_prompt)
        
        steps.append({"name": "reason", "result": response.content})
        
        return {
            "answer": response.content,
            "reasoning_visible": False,
            "steps": steps
        }
    
    def _execute_decomposition_chain(
        self,
        question: str,
        data_context: str,
        chat_history: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Execute decomposition chain (break into sub-questions)
        
        Best for: Complex multi-part questions
        """
        logger.debug("Executing decomposition chain...")
        
        # Decompose question
        sub_questions = self.decomposer.decompose(question)
        
        logger.info(f"Decomposed into {len(sub_questions)} sub-questions")
        
        # Answer each sub-question
        sub_answers = []
        
        for sq in sub_questions:
            logger.debug(f"Answering sub-question {sq['order']}: {sq['question'][:50]}...")
            
            # Use simple chain for each sub-question
            sub_result = self._execute_simple_chain(sq['question'], data_context)
            
            sub_answers.append({
                "question": sq['question'],
                "answer": sub_result['answer'],
                "order": sq['order']
            })
        
        # Recompose answers
        final_answer = self.decomposer.recompose_answer(sub_answers, question)
        
        return {
            "answer": final_answer,
            "reasoning_visible": True,
            "steps": [
                {"name": "decompose", "result": f"{len(sub_questions)} sub-questions"},
                {"name": "sub_answers", "result": sub_answers},
                {"name": "recompose", "result": "Final answer synthesized"}
            ],
            "sub_questions": sub_questions,
            "sub_answers": sub_answers
        }
    
    def _execute_cot_chain(
        self,
        question: str,
        data_context: str,
        chat_history: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Execute chain-of-thought chain (explicit reasoning)
        
        Best for: Analytical questions requiring explanation
        """
        logger.debug("Executing chain-of-thought chain...")
        
        # Use CoT reasoner
        cot_result = self.cot_reasoner.reason(
            question=question,
            data_context=data_context,
            chat_history=chat_history
        )
        
        # Format for display
        if chain_config.SHOW_REASONING_STEPS:
            answer = self.cot_reasoner.format_reasoning_for_display(cot_result)
        else:
            answer = cot_result['final_answer']
        
        return {
            "answer": answer,
            "reasoning_visible": chain_config.SHOW_REASONING_STEPS,
            "steps": [
                {"name": step_name, "result": step_content[:200] + "..." if len(str(step_content)) > 200 else step_content}
                for step_name, step_content in cot_result['steps'].items()
            ],
            "confidence": cot_result['confidence'],
            "reasoning_details": cot_result
        }
    
    def _execute_memory_augmented_chain(
        self,
        question: str,
        data_context: str,
        chat_history: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Execute memory-augmented chain (heavy memory integration)
        
        Best for: Questions referencing history, comparisons, preferences
        """
        logger.debug("Executing memory-augmented chain...")
        
        if not self.memory:
            logger.warning("No memory available, falling back to simple chain")
            return self._execute_simple_chain(question, data_context)
        
        steps = []
        
        # Step 1: Comprehensive memory retrieval
        memory_context = self.memory.retrieve_context(question, strategy="aggressive")
        steps.append({"name": "memory_retrieval", "result": "Retrieved from all memory tiers"})
        
        # Step 2: Format context
        formatted_context = self.memory.format_context_for_prompt(memory_context)
        
        # Step 3: Reason with memory
        memory_augmented_prompt = f"""Answer this question using the comprehensive context from memory.

QUESTION: {question}

MEMORY CONTEXT:
{formatted_context}

CURRENT DATA:
{data_context}

Important:
- Reference specific past conversations when relevant
- Compare to historical data if applicable
- Note any preferences or patterns learned
- Be specific about what you remember

ANSWER:"""
        
        from core.llm import get_chat_llm
        response = get_chat_llm().invoke(memory_augmented_prompt)
        
        steps.append({"name": "reason_with_memory", "result": response.content})
        
        return {
            "answer": response.content,
            "reasoning_visible": False,
            "steps": steps,
            "memory_context": memory_context,
            "memory_used": True
        }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _understand_question(self, question: str) -> str:
        """Quick question understanding"""
        from core.llm import get_chat_llm
        
        prompt = f"""Quickly analyze: {question}

Extract:
1. Intent (what they want)
2. Key entities
3. Type of answer needed

Be concise (2-3 sentences):"""
        
        response = get_chat_llm().invoke(prompt)
        return response.content
    
    def _update_stats(self, chain_type: ChainType, execution_time: float):
        """Update execution statistics"""
        self.stats['total_executions'] += 1
        self.stats['total_execution_time'] += execution_time
        
        # By chain type
        if chain_type.value not in self.stats['by_chain_type']:
            self.stats['by_chain_type'][chain_type.value] = {
                'count': 0,
                'total_time': 0.0
            }
        
        self.stats['by_chain_type'][chain_type.value]['count'] += 1
        self.stats['by_chain_type'][chain_type.value]['total_time'] += execution_time
        
        # Average
        self.stats['avg_execution_time'] = (
            self.stats['total_execution_time'] / self.stats['total_executions']
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        stats = self.stats.copy()
        
        # Calculate averages by chain type
        for chain_type, data in stats['by_chain_type'].items():
            if data['count'] > 0:
                data['avg_time'] = data['total_time'] / data['count']
        
        return stats
    
    def reset_statistics(self):
        """Reset execution statistics"""
        self.stats = {
            "total_executions": 0,
            "by_chain_type": {},
            "avg_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        logger.info("Statistics reset")


# Global instance
_sequential_chain_manager = None

def get_sequential_chain_manager(
    memory_manager: Optional[EnhancedMemoryManager] = None
) -> SequentialChainManager:
    """Get global sequential chain manager instance"""
    global _sequential_chain_manager
    if _sequential_chain_manager is None or memory_manager is not None:
        _sequential_chain_manager = SequentialChainManager(memory_manager)
    return _sequential_chain_manager
