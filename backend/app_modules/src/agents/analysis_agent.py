"""
Analysis Agent - Performs financial analysis on CSV data
Uses LangChain with Groq for intelligent analysis
"""

from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE
import pandas as pd
import json
import os
from dotenv import load_dotenv
load_dotenv()
class AnalysisAgent:
    """
    Intelligent agent for financial data analysis
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=GROQ_TEMPERATURE,
            api_key=GROQ_API_KEY
        )
    
    def analyze_financial_data(self, data_summary: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive financial analysis of the dataset
        """
        
        # Create analysis prompt
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional financial analyst. Analyze the provided dataset and give comprehensive insights.

Focus on:
1. Overall Financial Health (score 0-100)
2. Key Trends and Patterns
3. Risk Assessment (Low/Medium/High)
4. Notable Anomalies or Concerns
5. Actionable Recommendations

Be specific, data-driven, and professional."""),
            ("user", """Here is the financial dataset to analyze:

{data_summary}

Provide a detailed analysis in the following JSON format:
{{
    "health_score": <0-100>,
    "risk_level": "<Low/Medium/High>",
    "summary": "<brief 2-3 sentence summary>",
    "key_insights": ["<insight 1>", "<insight 2>", ...],
    "trends": ["<trend 1>", "<trend 2>", ...],
    "concerns": ["<concern 1>", "<concern 2>", ...],
    "recommendations": ["<recommendation 1>", "<recommendation 2>", ...]
}}

IMPORTANT: Return ONLY valid JSON, no additional text.""")
        ])
        
        # Create chain
        chain = analysis_prompt | self.llm | StrOutputParser()
        
        try:
            # Get analysis
            result = chain.invoke({"data_summary": data_summary})
            
            # Parse JSON
            # Clean up the result to extract JSON
            result = result.strip()
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(result)
            
            # Add numerical statistics
            analysis["statistics"] = self._calculate_statistics(df)
            analysis["domain"] = self._detect_domain(df)
            
            return analysis
            
        except Exception as e:
            # Fallback analysis
            return {
                "health_score": 50,
                "risk_level": "Medium",
                "summary": f"Analysis completed with limited insights due to: {str(e)}",
                "key_insights": ["Data processed successfully"],
                "trends": ["Further analysis required"],
                "concerns": ["Unable to perform deep analysis"],
                "recommendations": ["Review data quality and try again"],
                "statistics": self._calculate_statistics(df),
                "domain": "general",
                "error": str(e)
            }
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate basic statistics from dataframe"""
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": len(numeric_cols),
            "missing_values": int(df.isnull().sum().sum()),
            "completeness": round((1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100, 2)
        }
        
        if len(numeric_cols) > 0:
            stats["numeric_summary"] = {}
            for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
                stats["numeric_summary"][col] = {
                    "mean": round(df[col].mean(), 2),
                    "median": round(df[col].median(), 2),
                    "std": round(df[col].std(), 2)
                }
        
        return stats
    
    def _detect_domain(self, df: pd.DataFrame) -> str:
        """Detect the domain of the dataset"""
        columns_lower = [col.lower() for col in df.columns]
        
        # Financial keywords
        financial_keywords = ['amount', 'price', 'cost', 'revenue', 'expense', 
                            'income', 'balance', 'transaction', 'payment', 'salary']
        
        # Check for financial indicators
        financial_score = sum(1 for keyword in financial_keywords 
                            if any(keyword in col for col in columns_lower))
        
        if financial_score >= 2:
            return "finance"
        else:
            return "general"
    
    def generate_insights(self, question: str, context: str) -> str:
        """
        Generate insights based on a specific question and context
        """
        
        insight_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a financial data analyst. Provide clear, actionable insights based on the data."),
            ("user", """Context about the dataset:
{context}

User Question: {question}

Provide a detailed, data-driven answer. Be specific and reference actual numbers from the data when possible.""")
        ])
        
        chain = insight_prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({
                "context": context,
                "question": question
            })
            return result.strip()
        except Exception as e:
            return f"Unable to generate insights: {str(e)}"


class AnalysisOrchestrator:
    """
    Orchestrates the complete analysis pipeline
    """
    
    def __init__(self):
        self.agent = AnalysisAgent()
        self.current_analysis: Optional[Dict] = None
    
    def run_analysis(self, data_summary: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run complete analysis pipeline
        """
        # Perform analysis
        analysis = self.agent.analyze_financial_data(data_summary, df)
        
        # Store for later reference
        self.current_analysis = analysis
        
        return analysis
    
    def get_current_analysis(self) -> Optional[Dict]:
        """Get the most recent analysis"""
        return self.current_analysis


# Global orchestrator instance
analysis_orchestrator = AnalysisOrchestrator()
