"""
Chain-of-Thought Reasoner for Vishleshak AI v1
Implements explicit step-by-step reasoning with memory
"""

from typing import Dict, List, Any, Optional
import logging
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.llm import get_chat_llm
from core.enhanced_memory import EnhancedMemoryManager
from config import chain_config
from chatbot.prompt_templates import PERSONA_BLOCK

logger = logging.getLogger(__name__)


class ChainOfThoughtReasoner:
    """
    Chain-of-Thought reasoning with explicit step visibility
    
    Reasoning Steps:
    1. UNDERSTAND: What is being asked?
    2. DECOMPOSE: Break into sub-problems (if needed)
    3. RETRIEVE: Get relevant context from memory
    4. REASON: Perform step-by-step reasoning
    5. VALIDATE: Check reasoning consistency
    6. SYNTHESIZE: Formulate final answer
    
    Features:
    - Explicit reasoning steps
    - Memory integration at each step
    - Validation of logic
    - Transparent thinking process
    
    Usage:
        reasoner = ChainOfThoughtReasoner(memory_manager)
        result = reasoner.reason(question, data_context)
    """
    
    def __init__(self, memory_manager: Optional[EnhancedMemoryManager] = None):
        """
        Initialize CoT reasoner
        
        Args:
            memory_manager: Enhanced memory manager instance
        """
        self.memory = memory_manager
        self.llm = get_chat_llm()
        self.show_steps = chain_config.SHOW_REASONING_STEPS
        
        # Create prompts for each reasoning step
        self.prompts = self._create_step_prompts()
        
        logger.info("✅ Chain-of-thought reasoner initialized")
    
    def _create_step_prompts(self) -> Dict[str, ChatPromptTemplate]:
        """Create prompts for each reasoning step"""
        prompts = {}
        
        # STEP 1: UNDERSTAND
        prompts["understand"] = ChatPromptTemplate.from_messages([
            ("system", """Analyze this question and extract:
1. Main intent (what user wants to know)
2. Key entities mentioned
3. Type of analysis needed
4. Any constraints or conditions

Be concise and specific."""),
            ("human", "{question}")
        ])
        
        # STEP 4: REASON (main reasoning step)
        prompts["reason"] = ChatPromptTemplate.from_messages([
            ("system", """Think step-by-step to answer this question.

QUESTION UNDERSTANDING:
{understanding}

RELEVANT CONTEXT:
{context}

DATA AVAILABLE:
{data_context}

Think through this step-by-step:
1. What data do I need?
2. What calculations or analysis are required?
3. What patterns or insights should I look for?
4. What conclusions can I draw?

Show your reasoning clearly at each step."""),
            ("human", "Please reason through this: {question}")
        ])
        
        # STEP 5: VALIDATE
        prompts["validate"] = ChatPromptTemplate.from_messages([
            ("system", """Validate this reasoning for:
1. Logical consistency
2. Factual accuracy (against provided data)
3. Completeness (does it fully answer the question?)
4. Clarity and coherence

REASONING TO VALIDATE:
{reasoning}

ORIGINAL QUESTION:
{question}

Provide validation assessment:"""),
            ("human", "Is this reasoning sound?")
        ])
        
        # STEP 6: SYNTHESIZE
        prompts["synthesize"] = ChatPromptTemplate.from_messages([
            ("system", PERSONA_BLOCK + """
Synthesize the reasoning into a clear, direct answer.

QUESTION: {question}

REASONING STEPS:
{reasoning}

VALIDATION: {validation}

Provide a clear, well-structured answer that:
1. Directly answers the question
2. Includes specific data points/numbers
3. Is easy to understand
4. Is actionable (if applicable)"""),
            ("human", "What's the final answer?")
        ])
        
        return prompts
    
    def reason(
        self,
        question: str,
        data_context: str,
        chat_history: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Perform chain-of-thought reasoning
        
        Args:
            question: User's question
            data_context: Available data context
            chat_history: Conversation history
            
        Returns:
            Dict with reasoning steps and final answer
        """
        logger.info(f"🧠 Starting CoT reasoning for: {question[:50]}...")
        
        result = {
            "question": question,
            "steps": {},
            "final_answer": "",
            "confidence": 0.0
        }
        
        try:
            # STEP 1: UNDERSTAND
            result["steps"]["understand"] = self._step_understand(question)
            
            # STEP 2: DECOMPOSE (handled by QuestionDecomposer if needed)
            # For now, we'll skip explicit decomposition in CoT
            
            # STEP 3: RETRIEVE (get memory context)
            if self.memory:
                memory_context = self._step_retrieve(question)
                result["steps"]["retrieve"] = memory_context
            else:
                memory_context = {"message": "No memory available"}
                result["steps"]["retrieve"] = memory_context
            
            # STEP 4: REASON
            result["steps"]["reason"] = self._step_reason(
                question=question,
                understanding=result["steps"]["understand"],
                context=self._format_memory_context(memory_context),
                data_context=data_context
            )
            
            # STEP 5: VALIDATE
            if chain_config.ENABLE_VALIDATION:
                result["steps"]["validate"] = self._step_validate(
                    question=question,
                    reasoning=result["steps"]["reason"]
                )
                
                # Extract confidence from validation
                result["confidence"] = self._extract_confidence(
                    result["steps"]["validate"]
                )
            else:
                result["steps"]["validate"] = "Validation skipped"
                result["confidence"] = 0.7
            
            # STEP 6: SYNTHESIZE
            result["final_answer"] = self._step_synthesize(
                question=question,
                reasoning=result["steps"]["reason"],
                validation=result["steps"].get("validate", "Not validated")
            )
            
            logger.info(f"✅ CoT reasoning complete. Confidence: {result['confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"Error in CoT reasoning: {e}", exc_info=True)
            result["final_answer"] = f"Error in reasoning: {str(e)}"
            result["confidence"] = 0.0
        
        return result
    
    def _step_understand(self, question: str) -> str:
        """Step 1: Understand the question"""
        logger.debug("Step 1: Understanding question...")
        
        try:
            chain = self.prompts["understand"] | self.llm | StrOutputParser()
            understanding = chain.invoke({"question": question})
            
            return understanding
        
        except Exception as e:
            logger.error(f"Error in understand step: {e}")
            return f"Question: {question}"
    
    def _step_retrieve(self, question: str) -> Dict[str, Any]:
        """Step 3: Retrieve relevant context from memory"""
        logger.debug("Step 3: Retrieving context from memory...")
        
        if not self.memory:
            return {"message": "No memory available"}
        
        try:
            context = self.memory.retrieve_context(
                query=question,
                strategy=chain_config.DEFAULT_CHAIN_TYPE
            )
            
            return context
        
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {"error": str(e)}
    
    def _step_reason(
        self,
        question: str,
        understanding: str,
        context: str,
        data_context: str
    ) -> str:
        """Step 4: Perform reasoning"""
        logger.debug("Step 4: Reasoning...")
        
        try:
            chain = self.prompts["reason"] | self.llm | StrOutputParser()
            
            reasoning = chain.invoke({
                "question": question,
                "understanding": understanding,
                "context": context,
                "data_context": data_context
            })
            
            return reasoning
        
        except Exception as e:
            logger.error(f"Error in reasoning step: {e}")
            return f"Error: {str(e)}"
    
    def _step_validate(self, question: str, reasoning: str) -> str:
        """Step 5: Validate reasoning"""
        logger.debug("Step 5: Validating reasoning...")
        
        try:
            chain = self.prompts["validate"] | self.llm | StrOutputParser()
            
            validation = chain.invoke({
                "question": question,
                "reasoning": reasoning
            })
            
            return validation
        
        except Exception as e:
            logger.error(f"Error in validation step: {e}")
            return "Validation failed"
    
    def _step_synthesize(
        self,
        question: str,
        reasoning: str,
        validation: str
    ) -> str:
        """Step 6: Synthesize final answer"""
        logger.debug("Step 6: Synthesizing answer...")
        
        try:
            chain = self.prompts["synthesize"] | self.llm | StrOutputParser()
            
            answer = chain.invoke({
                "question": question,
                "reasoning": reasoning,
                "validation": validation
            })
            
            return answer
        
        except Exception as e:
            logger.error(f"Error in synthesis step: {e}")
            return reasoning  # Fallback to reasoning if synthesis fails
    
    def _format_memory_context(self, memory_context: Dict) -> str:
        """Format memory context for prompt"""
        if not memory_context or "error" in memory_context:
            return "No relevant context available."
        
        parts = []
        
        # Short-term memory
        if "short_term" in memory_context:
            parts.append("RECENT CONVERSATION:")
            # Format recent messages
            parts.append("(Recent discussion context)")
        
        # Long-term memory
        if "long_term" in memory_context and memory_context["long_term"]:
            parts.append("\nRELEVANT PAST CONVERSATIONS:")
            for i, conv in enumerate(memory_context["long_term"][:2], 1):
                parts.append(f"{i}. {conv['text'][:200]}...")
        
        # Semantic memory
        if "semantic" in memory_context and memory_context["semantic"]:
            parts.append("\nKNOWN FACTS:")
            for mem in memory_context["semantic"][:3]:
                parts.append(f"- {mem['value']}")
        
        return "\n".join(parts) if parts else "No relevant context."
    
    def _extract_confidence(self, validation: str) -> float:
        """Extract confidence score from validation"""
        # Simple heuristic: look for positive words
        positive_words = ['valid', 'correct', 'accurate', 'consistent', 'sound']
        negative_words = ['invalid', 'incorrect', 'inaccurate', 'inconsistent']
        
        validation_lower = validation.lower()
        
        positive_count = sum(1 for word in positive_words if word in validation_lower)
        negative_count = sum(1 for word in negative_words if word in validation_lower)
        
        if negative_count > 0:
            return 0.5
        elif positive_count > 2:
            return 0.9
        elif positive_count > 0:
            return 0.7
        else:
            return 0.6
    
    def format_reasoning_for_display(self, result: Dict[str, Any]) -> str:
        """Format reasoning steps for user display"""
        if not self.show_steps:
            return result["final_answer"]
        
        output = []
        
        # Add reasoning steps
        output.append("🧠 **Reasoning Process:**\n")
        
        for step_name, step_content in result["steps"].items():
            if isinstance(step_content, str):
                output.append(f"**{step_name.upper()}:**")
                output.append(step_content[:300] + "..." if len(step_content) > 300 else step_content)
                output.append("")
        
        # Add final answer
        output.append("**FINAL ANSWER:**")
        output.append(result["final_answer"])
        
        # Add confidence
        output.append(f"\n*Confidence: {result['confidence']:.0%}*")
        
        return "\n".join(output)


# Global instance
_cot_reasoner = None

def get_cot_reasoner(memory_manager: Optional[EnhancedMemoryManager] = None) -> ChainOfThoughtReasoner:
    """Get global CoT reasoner instance"""
    global _cot_reasoner
    if _cot_reasoner is None or memory_manager is not None:
        _cot_reasoner = ChainOfThoughtReasoner(memory_manager)
    return _cot_reasoner
