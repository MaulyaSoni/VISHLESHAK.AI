"""
Question Decomposer for Vishleshak AI v1
Breaks complex questions into manageable sub-questions
"""

from typing import List, Dict, Any, Optional
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.llm import get_chat_llm
from config import chain_config

logger = logging.getLogger(__name__)


class QuestionDecomposer:
    """
    Decompose complex questions into simpler sub-questions
    
    Strategies:
    1. Simple: Rule-based decomposition (fast)
    2. Smart: Hybrid rule + pattern matching
    3. LLM: Full LLM-based decomposition (thorough)
    
    Usage:
        decomposer = QuestionDecomposer()
        sub_questions = decomposer.decompose("Complex question here")
    """
    
    def __init__(self, strategy: str = "smart"):
        """
        Initialize question decomposer
        
        Args:
            strategy: Decomposition strategy ('simple', 'smart', 'llm')
        """
        self.strategy = strategy
        self.llm = get_chat_llm()
        self.llm_prompt = self._create_decomposition_prompt()
        logger.info(f"✅ Question decomposer initialized (strategy: {strategy})")
    
    def _create_decomposition_prompt(self) -> PromptTemplate:
        """Create prompt for LLM-based decomposition"""
        return PromptTemplate(
            input_variables=["question"],
            template="""Break down this complex question into simpler sub-questions.

QUESTION: {question}

Guidelines:
1. Create 2-5 sub-questions that, when answered together, fully answer the main question
2. Sub-questions should be independent and answerable separately
3. Order sub-questions logically (dependencies first)
4. Make each sub-question clear and specific

Format your response as a numbered list:
1. First sub-question
2. Second sub-question
...

SUB-QUESTIONS:"""
        )
    
    def decompose(self, question: str) -> List[Dict[str, Any]]:
        """
        Decompose question into sub-questions
        
        Args:
            question: Original complex question
            
        Returns:
            List of sub-question dicts with metadata
        """
        if not self._is_complex(question):
            # Question is simple enough
            return [{
                "question": question,
                "order": 1,
                "is_original": True,
                "dependencies": []
            }]
        
        # Route to appropriate strategy
        if self.strategy == "simple":
            sub_questions = self._decompose_simple(question)
        elif self.strategy == "smart":
            sub_questions = self._decompose_smart(question)
        else:  # llm
            sub_questions = self._decompose_llm(question)
        
        logger.info(f"Decomposed into {len(sub_questions)} sub-questions")
        return sub_questions
    
    def _is_complex(self, question: str) -> bool:
        """
        Determine if question is complex enough to decompose
        
        Args:
            question: Question to analyze
            
        Returns:
            True if complex
        """
        if not chain_config.ENABLE_DECOMPOSITION:
            return False
        
        # Check length
        if len(question.split()) < 10:
            return False
        
        # Check for complexity indicators
        question_lower = question.lower()
        indicator_count = sum(
            1 for indicator in chain_config.COMPLEX_QUESTION_INDICATORS
            if indicator in question_lower
        )
        
        # Check for multiple questions
        question_mark_count = question.count('?')
        
        # Calculate complexity score
        complexity = (
            indicator_count * 0.2 +
            question_mark_count * 0.3 +
            (len(question.split()) / 100)
        )
        
        is_complex = complexity >= chain_config.DECOMPOSITION_THRESHOLD
        
        logger.debug(f"Question complexity: {complexity:.2f}, is_complex: {is_complex}")
        return is_complex
    
    def _decompose_simple(self, question: str) -> List[Dict[str, Any]]:
        """
        Simple rule-based decomposition
        
        Splits on conjunctions and creates sub-questions
        """
        # Split on common conjunctions
        parts = []
        
        # Try to split on 'and'
        if ' and ' in question.lower():
            parts = question.split(' and ')
        # Try to split on 'also'
        elif ' also ' in question.lower():
            parts = question.split(' also ')
        # Try to split on multiple question marks
        elif question.count('?') > 1:
            parts = [p.strip() + '?' for p in question.split('?') if p.strip()]
        else:
            # Can't decompose simply
            parts = [question]
        
        # Format as sub-questions
        sub_questions = []
        for i, part in enumerate(parts, 1):
            sub_questions.append({
                "question": part.strip(),
                "order": i,
                "is_original": len(parts) == 1,
                "dependencies": list(range(1, i))  # Depends on all previous
            })
        
        return sub_questions
    
    def _decompose_smart(self, question: str) -> List[Dict[str, Any]]:
        """
        Smart hybrid decomposition
        
        Uses rules + pattern matching
        """
        # Start with simple decomposition
        simple_result = self._decompose_simple(question)
        
        # If simple didn't decompose, try pattern matching
        if len(simple_result) == 1:
            question_lower = question.lower()
            
            # Pattern: "Compare A and B"
            if 'compare' in question_lower:
                # Extract what to compare
                sub_questions = [
                    {
                        "question": "What are the characteristics of the first item?",
                        "order": 1,
                        "dependencies": []
                    },
                    {
                        "question": "What are the characteristics of the second item?",
                        "order": 2,
                        "dependencies": []
                    },
                    {
                        "question": f"Original: {question}",
                        "order": 3,
                        "dependencies": [1, 2]
                    }
                ]
                return sub_questions
            
            # Pattern: "Explain why/how X"
            elif any(word in question_lower for word in ['why', 'how', 'explain']):
                sub_questions = [
                    {
                        "question": "What is the current situation or fact?",
                        "order": 1,
                        "dependencies": []
                    },
                    {
                        "question": f"Original: {question}",
                        "order": 2,
                        "dependencies": [1]
                    }
                ]
                return sub_questions
        
        return simple_result
    
    def _decompose_llm(self, question: str) -> List[Dict[str, Any]]:
        """
        LLM-based decomposition
        
        Most thorough but slower
        """
        try:
            # Generate decomposition
            chain = self.llm_prompt | self.llm | StrOutputParser()
            result = chain.invoke({"question": question})
            
            # Parse numbered list
            sub_questions = []
            lines = result.strip().split('\n')
            
            order = 1
            for line in lines:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Check if line starts with number
                import re
                match = re.match(r'^\d+\.\s*(.+)$', line)
                if match:
                    sub_q = match.group(1).strip()
                    sub_questions.append({
                        "question": sub_q,
                        "order": order,
                        "dependencies": list(range(1, order)),
                        "is_original": False
                    })
                    order += 1
            
            # If parsing failed, return original
            if not sub_questions:
                return [{
                    "question": question,
                    "order": 1,
                    "is_original": True,
                    "dependencies": []
                }]
            
            return sub_questions
        
        except Exception as e:
            logger.error(f"Error in LLM decomposition: {e}")
            # Fallback to simple
            return self._decompose_simple(question)
    
    def recompose_answer(
        self,
        sub_answers: List[Dict[str, str]],
        original_question: str
    ) -> str:
        """
        Recompose sub-answers into final answer
        
        Args:
            sub_answers: List of {"question": str, "answer": str}
            original_question: Original complex question
            
        Returns:
            Synthesized final answer
        """
        if len(sub_answers) == 1:
            return sub_answers[0]["answer"]
        
        # Create synthesis prompt
        synthesis_prompt = f"""Synthesize these sub-answers into a comprehensive answer to the original question.

ORIGINAL QUESTION: {original_question}

SUB-ANSWERS:
"""
        for i, sa in enumerate(sub_answers, 1):
            synthesis_prompt += f"\n{i}. Q: {sa['question']}\n   A: {sa['answer']}\n"
        
        synthesis_prompt += "\nProvide a comprehensive, well-structured answer that addresses the original question:"
        
        try:
            # Generate synthesis
            response = self.llm.invoke(synthesis_prompt)
            
            return response.content
        
        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}")
            # Fallback: concatenate answers
            return "\n\n".join(sa["answer"] for sa in sub_answers)


# Global instance
_question_decomposer = None

def get_question_decomposer() -> QuestionDecomposer:
    """Get global question decomposer instance"""
    global _question_decomposer
    if _question_decomposer is None:
        _question_decomposer = QuestionDecomposer(
            strategy=chain_config.DECOMPOSITION_STRATEGY
        )
    return _question_decomposer
