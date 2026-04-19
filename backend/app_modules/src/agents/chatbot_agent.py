"""
OPTIMIZED Chatbot Agent - Bug fixes and improvements
Replace your existing src/agents/chatbot_agent.py with this file
"""

from typing import Dict, List, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE
from src.memory.conversation import ConversationMemory, get_conversation_memory
from src.core.data_processor import document_store
import pandas as pd


class ChatbotAgent:
    """
    OPTIMIZED: Conversational agent for Q&A about financial data
    Maintains context and provides intelligent responses
    """
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=GROQ_TEMPERATURE,
            api_key=GROQ_API_KEY
        )
        self.memory = get_conversation_memory(session_id)
        self.current_data_context: Optional[str] = None
        self.data_processor = None  # Store reference to data processor
    
    def set_data_context(self, data_summary: str, data_processor=None):
        """Set the current dataset context for the chatbot"""
        self.current_data_context = data_summary
        self.data_processor = data_processor
    
    def chat(self, user_message: str, use_rag: bool = True) -> str:
        """
        OPTIMIZED: Process a user message and return a response
        
        Args:
            user_message: The user's question or message
            use_rag: Whether to use RAG for retrieving relevant context
        
        Returns:
            The chatbot's response
        """
        
        # Add user message to memory
        self.memory.add_message("user", user_message)
        
        # Get conversation context
        chat_history = self._format_chat_history()
        
        # Get RAG context if enabled and available
        rag_context = ""
        if use_rag and document_store.documents:
            relevant_docs = document_store.search(user_message, top_k=3)
            if relevant_docs:
                rag_context = "\n\n".join([doc["content"] for doc in relevant_docs])
        
        # Get direct data if processor is available
        direct_data = ""
        if self.data_processor:
            direct_data = self._get_direct_data_answer(user_message)
        
        # Create the prompt with context
        system_message = self._create_system_message(rag_context, direct_data)
        
        # Create chat prompt
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", "{input}")
        ])
        
        # Create chain
        chain = chat_prompt | self.llm | StrOutputParser()
        
        try:
            # Generate response
            response = chain.invoke({
                "input": f"""Previous conversation:
{chat_history}

Current question: {user_message}

Provide a clear, direct answer based on the data provided."""
            })
            
            response = response.strip()
            
            # Add response to memory
            self.memory.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            self.memory.add_message("assistant", error_msg)
            return error_msg
    
    def _get_direct_data_answer(self, question: str) -> str:
        """
        OPTIMIZED: Get direct answers from the data for common questions
        """
        if not self.data_processor:
            return ""
        
        try:
            df = self.data_processor.get_dataframe()
            metadata = self.data_processor.get_metadata()
            question_lower = question.lower()
            
            # List columns
            if any(word in question_lower for word in ['columns', 'column names', 'what columns', 'list columns']):
                cols = ", ".join(metadata['columns'])
                return f"COLUMNS: {cols}"
            
            # List categories (if Category column exists)
            if 'category' in question_lower and 'Category' in df.columns:
                categories = df['Category'].unique().tolist()
                return f"CATEGORIES: {', '.join(str(c) for c in categories)}"
            
            # Total amount/sum
            if any(word in question_lower for word in ['total', 'sum']) and 'Amount' in df.columns:
                total = df['Amount'].sum()
                return f"TOTAL AMOUNT: ${total:,.2f}"
            
            # Income vs expenses
            if 'income' in question_lower and 'Type' in df.columns:
                income = df[df['Type'] == 'Credit']['Amount'].sum() if 'Credit' in df['Type'].values else 0
                return f"TOTAL INCOME: ${income:,.2f}"
            
            if 'expense' in question_lower and 'Type' in df.columns:
                expenses = df[df['Type'] == 'Debit']['Amount'].sum() if 'Debit' in df['Type'].values else 0
                return f"TOTAL EXPENSES: ${expenses:,.2f}"
            
            # Count rows
            if 'how many' in question_lower or 'count' in question_lower:
                return f"TOTAL TRANSACTIONS: {len(df)}"
            
            # Categories breakdown
            if 'by category' in question_lower and 'Category' in df.columns:
                category_totals = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
                result = "SPENDING BY CATEGORY:\n"
                for cat, amt in category_totals.head(10).items():
                    result += f"- {cat}: ${amt:,.2f}\n"
                return result
            
        except Exception as e:
            return f"Error extracting data: {str(e)}"
        
        return ""
    
    def _create_system_message(self, rag_context: str = "", direct_data: str = "") -> str:
        """OPTIMIZED: Create the system message with all available context"""
        
        base_message = """You are Vishleshak AI v1, an intelligent financial assistant analyzing uploaded financial data.

CRITICAL INSTRUCTIONS:
1. Use the provided data context to answer questions
2. Be specific and cite actual numbers from the data
3. If direct data is provided below, use it in your answer
4. Keep answers concise and clear
5. Don't make up information - only use what's provided"""
        
        if direct_data:
            base_message += f"\n\nDIRECT DATA ANSWER:\n{direct_data}"
        
        if self.current_data_context:
            base_message += f"\n\nDATASET CONTEXT:\n{self.current_data_context[:800]}"
        
        if rag_context:
            base_message += f"\n\nRELEVANT INFORMATION:\n{rag_context[:500]}"
        
        return base_message
    
    def _format_chat_history(self, max_messages: int = 6) -> str:
        """OPTIMIZED: Format recent chat history for context"""
        recent = self.memory.get_recent_messages(max_messages)
        
        if not recent:
            return "No previous conversation."
        
        formatted = []
        for msg in recent[-4:]:  # Only last 4 messages
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg['content'][:150]  # Truncate long messages
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def clear_conversation(self):
        """Clear the conversation history"""
        self.memory.clear_history()
    
    def get_conversation_summary(self) -> Dict:
        """Get a summary of the conversation"""
        return {
            "session_id": self.session_id,
            "message_count": self.memory.get_message_count(),
            "has_data_context": self.current_data_context is not None,
            "recent_messages": self.memory.get_recent_messages(5)
        }


class MultiTurnChatbot:
    """
    OPTIMIZED: Enhanced chatbot with multi-turn conversation support
    """
    
    def __init__(self, session_id: str = "default"):
        self.chatbot = ChatbotAgent(session_id)
        self.first_message = True
    
    def process_message(self, message: str, data_summary: str = None, data_processor=None) -> Dict[str, str]:
        """
        OPTIMIZED: Process a message and return structured response
        """
        
        # Update data context if provided
        if data_summary:
            self.chatbot.set_data_context(data_summary, data_processor)
        
        # Only show greeting on very first message and if it's actually a greeting
        if self.first_message and self._is_greeting(message):
            self.first_message = False
            return {
                "response": self._generate_greeting(),
                "type": "greeting",
                "suggestions": [
                    "What columns are in my dataset?",
                    "What categories are present?",
                    "Show me total income and expenses"
                ]
            }
        
        # Mark that we've had first interaction
        self.first_message = False
        
        # Check if this is a request for help
        if self._is_help_request(message):
            return {
                "response": self._generate_help_message(),
                "type": "help"
            }
        
        # Process normal question
        response = self.chatbot.chat(message)
        
        return {
            "response": response,
            "type": "answer"
        }
    
    def _is_greeting(self, message: str) -> bool:
        """OPTIMIZED: Check if message is ONLY a greeting (no question)"""
        message_lower = message.lower().strip()
        
        # Pure greetings (no questions)
        pure_greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 
                         'good afternoon', 'good evening', 'hi there', 'hello there']
        
        # If message is exactly a greeting and nothing else
        if message_lower in pure_greetings:
            return True
        
        # If message has a question mark or is longer than 15 chars, it's not just a greeting
        if '?' in message or len(message) > 15:
            return False
        
        return False
    
    def _is_help_request(self, message: str) -> bool:
        """Check if message is asking for help"""
        help_keywords = ['help', 'how to use', 'what can you do', 'guide', 'assist me']
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in help_keywords)
    
    def _generate_greeting(self) -> str:
        """Generate a friendly greeting"""
        return """Hello! I'm Vishleshak AI v1 👋

I can answer questions about your financial data:
- "What columns are in my dataset?"
- "What are the total expenses?"
- "Show me spending by category"

What would you like to know?"""
    
    def _generate_help_message(self) -> str:
        """Generate help message"""
        return """**Here's what I can help with:**

📊 **Dataset Questions**
- "What columns are in my data?"
- "What categories exist?"
- "How many transactions?"

💰 **Financial Analysis**
- "What's the total income?"
- "What are the total expenses?"
- "Show spending by category"

📈 **Trends & Insights**
- "What's the average transaction?"
- "What's the biggest expense?"

Just ask naturally - I'll understand!"""
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the full conversation history"""
        return self.chatbot.memory.get_all_messages()
    
    def clear_conversation(self):
        """Clear the conversation"""
        self.chatbot.clear_conversation()
        self.first_message = True


# Global chatbot instance
_chatbot_instances: Dict[str, MultiTurnChatbot] = {}


def get_chatbot(session_id: str = "default") -> MultiTurnChatbot:
    """Get or create a chatbot instance for a session"""
    if session_id not in _chatbot_instances:
        _chatbot_instances[session_id] = MultiTurnChatbot(session_id)
    return _chatbot_instances[session_id]