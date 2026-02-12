"""
CSV Data Processor with RAG (Retrieval Augmented Generation)
Handles CSV/Excel file processing and creates queryable knowledge base
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import json


class DataProcessor:
    """Process and analyze CSV/Excel files"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.df: Optional[pd.DataFrame] = None
        self.metadata: Dict = {}
        self.load_data()
    
    def load_data(self):
        """Load data from file"""
        try:
            if self.file_path.suffix.lower() == '.csv':
                self.df = pd.read_csv(self.file_path)
            elif self.file_path.suffix.lower() in ['.xlsx', '.xls']:
                self.df = pd.read_excel(self.file_path)
            else:
                raise ValueError(f"Unsupported file type: {self.file_path.suffix}")
            
            self._generate_metadata()
        except Exception as e:
            raise Exception(f"Error loading file: {str(e)}")
    
    def _generate_metadata(self):
        """Generate comprehensive metadata about the dataset"""
        if self.df is None:
            return
        
        self.metadata = {
            "filename": self.file_path.name,
            "shape": {
                "rows": len(self.df),
                "columns": len(self.df.columns)
            },
            "columns": list(self.df.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
            "missing_values": self.df.isnull().sum().to_dict(),
            "numeric_columns": list(self.df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": list(self.df.select_dtypes(include=['object']).columns),
            "date_columns": list(self.df.select_dtypes(include=['datetime64']).columns),
        }
        
        # Add summary statistics for numeric columns
        if self.metadata["numeric_columns"]:
            self.metadata["statistics"] = {}
            for col in self.metadata["numeric_columns"]:
                self.metadata["statistics"][col] = {
                    "mean": float(self.df[col].mean()) if not self.df[col].isnull().all() else None,
                    "median": float(self.df[col].median()) if not self.df[col].isnull().all() else None,
                    "std": float(self.df[col].std()) if not self.df[col].isnull().all() else None,
                    "min": float(self.df[col].min()) if not self.df[col].isnull().all() else None,
                    "max": float(self.df[col].max()) if not self.df[col].isnull().all() else None,
                }
    
    def get_summary(self) -> str:
        """Get a text summary of the dataset"""
        if self.df is None:
            return "No data loaded"
        
        summary = f"""
Dataset: {self.metadata['filename']}
Shape: {self.metadata['shape']['rows']} rows × {self.metadata['shape']['columns']} columns

Columns: {', '.join(self.metadata['columns'])}

Numeric Columns: {', '.join(self.metadata['numeric_columns']) if self.metadata['numeric_columns'] else 'None'}
Categorical Columns: {', '.join(self.metadata['categorical_columns']) if self.metadata['categorical_columns'] else 'None'}

Missing Values:
{chr(10).join(f"  - {col}: {count}" for col, count in self.metadata['missing_values'].items() if count > 0)}

Sample Data (first 5 rows):
{self.df.head().to_string()}
"""
        return summary.strip()
    
    def get_column_info(self, column: str) -> Dict:
        """Get detailed information about a specific column"""
        if self.df is None or column not in self.df.columns:
            return {}
        
        col_data = self.df[column]
        info = {
            "name": column,
            "dtype": str(col_data.dtype),
            "missing": int(col_data.isnull().sum()),
            "unique_values": int(col_data.nunique()),
        }
        
        if column in self.metadata.get("numeric_columns", []):
            info.update(self.metadata["statistics"].get(column, {}))
        elif column in self.metadata.get("categorical_columns", []):
            value_counts = col_data.value_counts().head(10).to_dict()
            info["top_values"] = {str(k): int(v) for k, v in value_counts.items()}
        
        return info
    
    def query_data(self, question: str) -> Dict[str, Any]:
        """
        Process natural language questions about the data
        Returns relevant data subset and metadata
        """
        # Simple keyword-based retrieval (can be enhanced with embeddings)
        question_lower = question.lower()
        
        result = {
            "question": question,
            "metadata": self.metadata,
            "relevant_columns": [],
            "data_sample": None,
            "statistics": {}
        }
        
        # Find relevant columns based on keywords
        for col in self.df.columns:
            if col.lower() in question_lower:
                result["relevant_columns"].append(col)
        
        # If specific columns found, provide their data
        if result["relevant_columns"]:
            result["data_sample"] = self.df[result["relevant_columns"]].head(10).to_dict('records')
            
            # Add statistics for numeric columns
            for col in result["relevant_columns"]:
                if col in self.metadata["numeric_columns"]:
                    result["statistics"][col] = self.metadata["statistics"].get(col, {})
        else:
            # Return full dataset summary
            result["data_sample"] = self.df.head(10).to_dict('records')
        
        return result
    
    def get_dataframe(self) -> pd.DataFrame:
        """Get the raw dataframe"""
        return self.df
    
    def get_metadata(self) -> Dict:
        """Get metadata dictionary"""
        return self.metadata


class DocumentStore:
    """
    Simple document store for RAG
    Stores processed documents in memory with basic retrieval
    """
    
    def __init__(self):
        self.documents: List[Dict] = []
    
    def add_document(self, content: str, metadata: Dict = None):
        """Add a document to the store"""
        doc = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": pd.Timestamp.now().isoformat()
        }
        self.documents.append(doc)
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Simple keyword-based search
        (Can be enhanced with embeddings for semantic search)
        """
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            
            # Simple relevance scoring based on keyword matches
            score = sum(1 for word in query_lower.split() if word in content_lower)
            
            if score > 0:
                results.append({
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "score": score
                })
        
        # Sort by score and return top k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def clear(self):
        """Clear all documents"""
        self.documents = []


# Global document store instance
document_store = DocumentStore()


def process_file_for_rag(file_path: str) -> DataProcessor:
    """
    Process a file and add it to the RAG system
    Returns DataProcessor for further analysis
    """
    processor = DataProcessor(file_path)
    
    # Add dataset summary to document store
    document_store.add_document(
        content=processor.get_summary(),
        metadata={
            "type": "dataset_summary",
            "filename": processor.metadata["filename"],
            "columns": processor.metadata["columns"]
        }
    )
    
    # Add column-specific information
    for col in processor.metadata["columns"]:
        col_info = processor.get_column_info(col)
        col_summary = f"Column '{col}': {json.dumps(col_info)}"
        document_store.add_document(
            content=col_summary,
            metadata={
                "type": "column_info",
                "column": col,
                "filename": processor.metadata["filename"]
            }
        )
    
    return processor
