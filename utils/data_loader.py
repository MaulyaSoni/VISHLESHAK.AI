"""
Data Loader for FINBOT v4
Handles file loading and validation

Features:
- CSV and Excel support
- File validation
- Size checking
- Error handling
"""

import pandas as pd
import os
from typing import Tuple, Optional, Dict, Any
from config import settings


class DataLoader:
    """
    Handles data file loading and validation
    """
    
    @staticmethod
    def load_file(file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Load a CSV or Excel file
        
        Args:
            file_path: Path to the file
        
        Returns:
            Tuple of (DataFrame, error_message)
            If successful: (DataFrame, None)
            If error: (None, error_message)
        """
        
        # Check if file exists
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            return None, f"File too large ({file_size_mb:.1f} MB). Maximum allowed: {settings.MAX_FILE_SIZE_MB} MB"
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Check supported formats
        if ext not in settings.SUPPORTED_FORMATS:
            return None, f"Unsupported file format: {ext}. Supported formats: {', '.join(settings.SUPPORTED_FORMATS)}"
        
        # Load file based on extension
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                return None, f"Unsupported file extension: {ext}"
            
            # Validate DataFrame
            if df.empty:
                return None, "File is empty"
            
            if len(df.columns) == 0:
                return None, "No columns found in file"
            
            return df, None
        
        except pd.errors.EmptyDataError:
            return None, "File is empty or has no data"
        
        except pd.errors.ParserError as e:
            return None, f"Error parsing file: {str(e)}"
        
        except Exception as e:
            return None, f"Error loading file: {str(e)}"
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        Get information about a file
        
        Args:
            file_path: Path to the file
        
        Returns:
            Dictionary with file information
        """
        if not os.path.exists(file_path):
            return {
                'exists': False,
                'error': 'File not found'
            }
        
        try:
            file_size_bytes = os.path.getsize(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            _, ext = os.path.splitext(file_path)
            
            return {
                'exists': True,
                'size_bytes': file_size_bytes,
                'size_mb': f"{file_size_mb:.2f}",
                'extension': ext,
                'filename': os.path.basename(file_path),
                'supported': ext.lower() in settings.SUPPORTED_FORMATS
            }
        
        except Exception as e:
            return {
                'exists': True,
                'error': str(e)
            }
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate a DataFrame
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        if df is None:
            return False, "DataFrame is None"
        
        if df.empty:
            return False, "DataFrame is empty"
        
        if len(df.columns) == 0:
            return False, "DataFrame has no columns"
        
        return True, "DataFrame is valid"
    
    @staticmethod
    def get_dataframe_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary information about a DataFrame
        
        Args:
            df: DataFrame to summarize
        
        Returns:
            Dictionary with summary information
        """
        return {
            'rows': len(df),
            'columns': len(df.columns),
            'numeric_columns': len(df.select_dtypes(include=['number']).columns),
            'categorical_columns': len(df.select_dtypes(include=['object', 'category']).columns),
            'datetime_columns': len(df.select_dtypes(include=['datetime64']).columns),
            'total_cells': len(df) * len(df.columns),
            'missing_cells': df.isnull().sum().sum(),
            'missing_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'column_names': df.columns.tolist()
        }
    
    @staticmethod
    def clean_dataframe_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean DataFrame to avoid Arrow serialization warnings
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Fix object columns that might cause issues
        for col in df.select_dtypes(include=['object']).columns:
            # Convert mixed types to string
            df[col] = df[col].astype(str)
        
        # Fix index if it causes issues
        if df.index.name == 'Row Labels' or 'Row Labels' in df.columns:
            df = df.reset_index(drop=True)
        
        return df