"""
Q&A Chain for FINBOT v4
Conversational AI with data analysis capabilities

Features:
- Conversational Q&A about datasets
- Persistent memory across sessions
- Auto-analysis when needed
- Context-aware responses
- Integration with data analysis tools
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from core.llm import get_chat_llm
from core.memory import ConversationManager
import json


class DataQAChain:
    """
    Q&A chain for conversational data analysis
    """
    
    def __init__(self, session_id: str, df: pd.DataFrame):
        """
        Initialize Q&A chain
        
        Args:
            session_id: Unique session identifier
            df: Pandas DataFrame to analyze
        """
        self.session_id = session_id
        self.df = df
        self.llm = get_chat_llm()
        self.conversation_manager = ConversationManager(session_id)
        
        # Prepare data context
        self.data_context = self._prepare_data_context()
    
    def _prepare_data_context(self) -> str:
        """
        Prepare comprehensive data context for LLM
        """
        context_parts = []
        
        # Basic info
        context_parts.append(f"## Dataset Overview")
        context_parts.append(f"- Total Rows: {len(self.df):,}")
        context_parts.append(f"- Total Columns: {len(self.df.columns)}")
        
        # Column information
        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        context_parts.append(f"\n## Columns")
        context_parts.append(f"**Numeric Columns ({len(numeric_cols)}):** {', '.join(numeric_cols)}")
        context_parts.append(f"**Categorical Columns ({len(categorical_cols)}):** {', '.join(categorical_cols)}")
        
        # Quick statistics for numeric columns
        if numeric_cols:
            context_parts.append(f"\n## Numeric Column Statistics")
            for col in numeric_cols[:10]:  # Limit to first 10
                stats = self.df[col].describe()
                context_parts.append(
                    f"- **{col}**: mean={stats['mean']:.2f}, "
                    f"min={stats['min']:.2f}, max={stats['max']:.2f}, "
                    f"std={stats['std']:.2f}"
                )
        
        # Categorical summaries
        if categorical_cols:
            context_parts.append(f"\n## Categorical Column Info")
            for col in categorical_cols[:10]:  # Limit to first 10
                unique_count = self.df[col].nunique()
                most_common = self.df[col].mode()[0] if len(self.df[col].mode()) > 0 else "N/A"
                context_parts.append(
                    f"- **{col}**: {unique_count} unique values, "
                    f"most common='{most_common}'"
                )
        
        # Missing data
        missing = self.df.isnull().sum()
        if missing.sum() > 0:
            context_parts.append(f"\n## Missing Data")
            for col in missing[missing > 0].index:
                context_parts.append(f"- {col}: {missing[col]} missing values")
        
        # Sample data (first few rows)
        context_parts.append(f"\n## Sample Data (first 3 rows)")
        context_parts.append(self.df.head(3).to_string())
        
        return "\n".join(context_parts)
    
    def ask(self, question: str) -> str:
        """
        Ask a question about the data
        
        Args:
            question: User's question
        
        Returns:
            AI response
        """
        
        # Prepare prompt
        system_template = """You are FINBOT, an expert data analyst assistant. You help users understand their data by answering questions accurately and clearly.

You have access to the following dataset:

{data_context}

**Your Role:**
- Answer questions about this specific dataset
- Provide accurate statistics and insights
- Be conversational but professional
- If you need to perform calculations, show your work
- If you don't know something, say so honestly

**Guidelines:**
- Use specific numbers from the dataset
- Format numbers clearly (use commas for thousands)
- Explain statistical concepts when needed
- Give context to your answers

Remember: You're analyzing THIS specific dataset, so all answers should be based on the data provided above.
"""
        
        human_template = """Question: {question}

Please provide a clear, accurate answer based on the dataset information."""
        
        # Get conversation history
        history = self.conversation_manager.get_history()
        
        # Format history for prompt
        history_text = ""
        if history:
            recent_history = history[-6:]  # Last 3 exchanges
            history_parts = []
            for msg in recent_history:
                if msg['type'] == 'human':
                    history_parts.append(f"User: {msg['content']}")
                else:
                    history_parts.append(f"Assistant: {msg['content']}")
            history_text = "\n".join(history_parts)
        
        # Build full prompt
        full_prompt = f"""{system_template.format(data_context=self.data_context)}

Previous conversation:
{history_text if history_text else "(No previous conversation)"}

{human_template.format(question=question)}
"""
        
        # Get response
        try:
            response = self.llm.invoke(full_prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Save to memory
            self.conversation_manager.add_exchange(question, answer)
            
            return answer
        
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            self.conversation_manager.add_exchange(question, error_msg)
            return error_msg
    
    def ask_with_data_analysis(self, question: str) -> str:
        """
        Ask a question with automatic data analysis if needed
        
        Args:
            question: User's question
        
        Returns:
            AI response with analysis
        """
        
        # Check if question requires statistical analysis
        analysis_keywords = ['average', 'mean', 'median', 'sum', 'total', 'count', 
                            'max', 'min', 'correlation', 'distribution', 'trend']
        
        needs_analysis = any(keyword in question.lower() for keyword in analysis_keywords)
        
        if needs_analysis:
            # Perform quick analysis
            analysis_result = self._perform_quick_analysis(question)
            
            # Enhance question with analysis results
            enhanced_question = f"{question}\n\nRelevant Analysis:\n{analysis_result}"
            
            return self.ask(enhanced_question)
        else:
            return self.ask(question)
    
    def _perform_quick_analysis(self, question: str) -> str:
        """
        Perform quick data analysis based on question
        
        Args:
            question: User's question
        
        Returns:
            Analysis results as string
        """
        results = []
        
        # Look for column mentions
        for col in self.df.columns:
            if col.lower() in question.lower():
                if self.df[col].dtype in ['int64', 'float64']:
                    # Numeric column
                    stats = self.df[col].describe()
                    results.append(
                        f"{col}: mean={stats['mean']:.2f}, "
                        f"median={stats['50%']:.2f}, "
                        f"min={stats['min']:.2f}, "
                        f"max={stats['max']:.2f}, "
                        f"std={stats['std']:.2f}"
                    )
                else:
                    # Categorical column
                    value_counts = self.df[col].value_counts()
                    results.append(
                        f"{col}: {len(value_counts)} unique values, "
                        f"top value='{value_counts.index[0]}' ({value_counts.iloc[0]} occurrences)"
                    )
        
        return "\n".join(results) if results else "No specific column analysis performed."
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_manager.get_history()
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_manager.clear()
    
    def get_summary(self) -> str:
        """Get conversation summary"""
        history = self.get_chat_history()
        
        if not history:
            return "No conversation yet."
        
        user_messages = sum(1 for m in history if m['type'] == 'human')
        
        return f"This conversation has {user_messages} questions and {len(history)} total messages."


class DataContextManager:
    """
    Manages data contexts for Q&A sessions
    """
    
    def __init__(self):
        """Initialize context manager"""
        self.contexts: Dict[str, DataQAChain] = {}
    
    def create_context(self, session_id: str, df: pd.DataFrame) -> DataQAChain:
        """
        Create or get a data context for a session
        
        Args:
            session_id: Session identifier
            df: DataFrame to analyze
        
        Returns:
            DataQAChain instance
        """
        if session_id in self.contexts:
            # Update DataFrame for existing context
            self.contexts[session_id].df = df
            self.contexts[session_id].data_context = self.contexts[session_id]._prepare_data_context()
        else:
            # Create new context
            self.contexts[session_id] = DataQAChain(session_id, df)
        
        return self.contexts[session_id]
    
    def get_context(self, session_id: str) -> Optional[DataQAChain]:
        """Get existing context"""
        return self.contexts.get(session_id)
    
    def remove_context(self, session_id: str):
        """Remove a context"""
        if session_id in self.contexts:
            del self.contexts[session_id]
    
    def clear_all(self):
        """Clear all contexts"""
        self.contexts.clear()
