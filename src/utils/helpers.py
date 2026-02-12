"""
Utility Functions for FINBOT
Common helper functions used across the application
"""

import pandas as pd
from typing import Optional, Tuple
from pathlib import Path


def validate_file(file_path: str, max_size_mb: float = 10) -> Tuple[bool, str]:
    """
    Validate uploaded file
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return False, "File does not exist"
    
    # Check file extension
    valid_extensions = ['.csv', '.xlsx', '.xls']
    if path.suffix.lower() not in valid_extensions:
        return False, f"Invalid file type. Supported: {', '.join(valid_extensions)}"
    
    # Check file size
    file_size_mb = path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    
    return True, ""


def format_number(num: float, decimals: int = 2) -> str:
    """Format number with proper thousand separators"""
    if pd.isna(num):
        return "N/A"
    
    if abs(num) >= 1_000_000:
        return f"${num/1_000_000:.{decimals}f}M"
    elif abs(num) >= 1_000:
        return f"${num/1_000:.{decimals}f}K"
    else:
        return f"${num:.{decimals}f}"


def detect_date_columns(df: pd.DataFrame) -> list:
    """Detect columns that might contain dates"""
    date_columns = []
    
    for col in df.columns:
        # Check if column name suggests it's a date
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['date', 'time', 'day', 'month', 'year']):
            date_columns.append(col)
            continue
        
        # Try to parse a sample of the column
        try:
            sample = df[col].dropna().head(10)
            pd.to_datetime(sample, errors='raise')
            date_columns.append(col)
        except:
            continue
    
    return date_columns


def detect_amount_columns(df: pd.DataFrame) -> list:
    """Detect columns that represent monetary amounts"""
    amount_columns = []
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Check column name for monetary keywords
        monetary_keywords = ['amount', 'price', 'cost', 'revenue', 'expense', 
                            'income', 'balance', 'payment', 'salary', 'total', 'sum']
        
        if any(keyword in col_lower for keyword in monetary_keywords):
            if pd.api.types.is_numeric_dtype(df[col]):
                amount_columns.append(col)
    
    return amount_columns


def create_data_summary_text(df: pd.DataFrame, max_rows: int = 5) -> str:
    """Create a comprehensive text summary of the dataframe"""
    
    summary_parts = []
    
    # Basic info
    summary_parts.append(f"Dataset has {len(df)} rows and {len(df.columns)} columns.")
    summary_parts.append(f"\nColumns: {', '.join(df.columns.tolist())}")
    
    # Data types
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if numeric_cols:
        summary_parts.append(f"\nNumeric columns: {', '.join(numeric_cols)}")
    if categorical_cols:
        summary_parts.append(f"\nCategorical columns: {', '.join(categorical_cols)}")
    
    # Missing values
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if len(missing_cols) > 0:
        summary_parts.append(f"\nMissing values: {dict(missing_cols)}")
    
    # Sample data
    summary_parts.append(f"\nFirst {max_rows} rows:")
    summary_parts.append(df.head(max_rows).to_string())
    
    # Statistics for numeric columns
    if numeric_cols:
        summary_parts.append("\nNumeric Statistics:")
        summary_parts.append(df[numeric_cols].describe().to_string())
    
    return "\n".join(summary_parts)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean dataframe by handling common issues
    """
    df_clean = df.copy()
    
    # Remove completely empty rows
    df_clean = df_clean.dropna(how='all')
    
    # Remove duplicate rows
    df_clean = df_clean.drop_duplicates()
    
    # Strip whitespace from string columns
    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].str.strip()
    
    # Convert date columns
    date_cols = detect_date_columns(df_clean)
    for col in date_cols:
        try:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
        except:
            pass
    
    return df_clean


def get_insights_from_dataframe(df: pd.DataFrame) -> dict:
    """
    Extract quick insights from dataframe
    """
    insights = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "numeric_columns": len(df.select_dtypes(include=['number']).columns),
        "categorical_columns": len(df.select_dtypes(include=['object']).columns),
        "missing_percentage": round((df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100, 2),
        "duplicate_rows": df.duplicated().sum(),
    }
    
    # Find columns with high missing values
    missing_pct = (df.isnull().sum() / len(df)) * 100
    insights["high_missing_columns"] = missing_pct[missing_pct > 20].to_dict()
    
    return insights


def create_summary_statistics(df: pd.DataFrame) -> dict:
    """
    Create summary statistics for numeric columns
    """
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    if len(numeric_cols) == 0:
        return {}
    
    stats = {}
    for col in numeric_cols:
        stats[col] = {
            "mean": round(df[col].mean(), 2),
            "median": round(df[col].median(), 2),
            "std": round(df[col].std(), 2),
            "min": round(df[col].min(), 2),
            "max": round(df[col].max(), 2),
            "missing": int(df[col].isnull().sum())
        }
    
    return stats
