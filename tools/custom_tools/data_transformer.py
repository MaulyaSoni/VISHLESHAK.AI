"""
Data Transformer Tool for FINBOT v4
Performs data transformations using pandas
"""

from typing import Any, Dict, Optional, List, Union
import pandas as pd
import numpy as np
import logging
from tools.custom_tools.base_tool import BaseTool
from config import tool_config

logger = logging.getLogger(__name__)


class DataTransformerTool(BaseTool):
    """
    Transform data using pandas operations
    
    Supported operations:
    - filter: Filter rows by condition
    - sort: Sort by columns
    - group_by: Group and aggregate
    - fillna: Fill missing values
    - dropna: Remove missing values
    - normalize: Normalize numeric columns
    - one_hot: One-hot encode categorical columns
    
    Usage:
        tool = DataTransformerTool()
        result = tool.run(
            df=dataframe,
            operation="filter",
            condition="attendance > 70"
        )
    """
    
    def __init__(self):
        super().__init__(
            name="data_transformer",
            description=(
                "Transform and manipulate data using pandas operations. "
                "Supports filtering, sorting, grouping, aggregation, "
                "handling missing values, normalization, and encoding. "
                "Always works on a copy of the data (non-destructive). "
                "Input should specify operation and parameters."
            ),
            category="data"
        )
        self.max_rows = tool_config.MAX_ROWS_TRANSFORM
    
    def run(
        self,
        df: pd.DataFrame,
        operation: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        Perform data transformation
        
        Args:
            df: DataFrame to transform
            operation: Operation to perform
            **kwargs: Operation-specific parameters
            
        Returns:
            Transformed DataFrame
        """
        if not tool_config.ENABLE_DATA_TRANSFORMATION:
            raise ValueError("Data transformation is disabled")
        
        # Check size limit
        if len(df) > self.max_rows:
            raise ValueError(f"DataFrame too large: {len(df)} rows (max: {self.max_rows})")
        
        # Always work on a copy
        df = df.copy()
        
        operation = operation.lower().strip()
        
        try:
            # Route to appropriate transformation
            if operation == "filter":
                result = self._filter(df, **kwargs)
            
            elif operation == "sort":
                result = self._sort(df, **kwargs)
            
            elif operation == "group_by":
                result = self._group_by(df, **kwargs)
            
            elif operation == "fillna":
                result = self._fillna(df, **kwargs)
            
            elif operation == "dropna":
                result = self._dropna(df, **kwargs)
            
            elif operation == "normalize":
                result = self._normalize(df, **kwargs)
            
            elif operation == "standardize":
                result = self._standardize(df, **kwargs)
            
            elif operation == "one_hot":
                result = self._one_hot_encode(df, **kwargs)
            
            elif operation == "create_column":
                result = self._create_column(df, **kwargs)
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            logger.info(f"Transformed data: {operation}")
            return result
        
        except Exception as e:
            logger.error(f"Error transforming data: {e}")
            raise
    
    def _filter(self, df: pd.DataFrame, condition: str = None, column: str = None, 
                operator: str = None, value: Any = None, **kwargs) -> pd.DataFrame:
        """
        Filter rows by condition
        
        Two modes:
        1. condition: "attendance > 70"
        2. column, operator, value: "attendance", ">", 70
        """
        if condition:
            # Parse condition and filter
            return df.query(condition)
        
        elif column and operator and value is not None:
            # Build condition
            if operator == ">":
                return df[df[column] > value]
            elif operator == ">=":
                return df[df[column] >= value]
            elif operator == "<":
                return df[df[column] < value]
            elif operator == "<=":
                return df[df[column] <= value]
            elif operator == "==":
                return df[df[column] == value]
            elif operator == "!=":
                return df[df[column] != value]
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        
        else:
            raise ValueError("Must provide either 'condition' or 'column, operator, value'")
    
    def _sort(self, df: pd.DataFrame, by: Union[str, List[str]], 
              ascending: bool = True, **kwargs) -> pd.DataFrame:
        """Sort by columns"""
        return df.sort_values(by=by, ascending=ascending)
    
    def _group_by(self, df: pd.DataFrame, by: Union[str, List[str]], 
                  agg: Dict[str, str], **kwargs) -> pd.DataFrame:
        """
        Group and aggregate
        
        Args:
            by: Column(s) to group by
            agg: Aggregation dict, e.g., {"sales": "sum", "profit": "mean"}
        """
        return df.groupby(by).agg(agg).reset_index()
    
    def _fillna(self, df: pd.DataFrame, value: Any = None, 
                method: str = None, **kwargs) -> pd.DataFrame:
        """
        Fill missing values
        
        Args:
            value: Value to fill (can be dict for per-column)
            method: 'ffill', 'bfill', 'mean', 'median', 'mode'
        """
        if value is not None:
            return df.fillna(value)
        
        elif method == "ffill":
            return df.ffill()
        
        elif method == "bfill":
            return df.bfill()
        
        elif method == "mean":
            numeric_cols = df.select_dtypes(include=['number']).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
            return df
        
        elif method == "median":
            numeric_cols = df.select_dtypes(include=['number']).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
            return df
        
        elif method == "mode":
            for col in df.columns:
                if df[col].isnull().any():
                    df[col] = df[col].fillna(df[col].mode()[0])
            return df
        
        else:
            raise ValueError("Must provide either 'value' or valid 'method'")
    
    def _dropna(self, df: pd.DataFrame, axis: int = 0, 
                how: str = "any", **kwargs) -> pd.DataFrame:
        """Drop rows/columns with missing values"""
        return df.dropna(axis=axis, how=how)
    
    def _normalize(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                   **kwargs) -> pd.DataFrame:
        """
        Normalize numeric columns to 0-1 range
        
        Args:
            columns: Columns to normalize (default: all numeric)
        """
        if columns is None:
            columns = df.select_dtypes(include=['number']).columns.tolist()
        
        for col in columns:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val - min_val != 0:
                df[col] = (df[col] - min_val) / (max_val - min_val)
        
        return df
    
    def _standardize(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                     **kwargs) -> pd.DataFrame:
        """
        Standardize numeric columns (z-score)
        
        Args:
            columns: Columns to standardize (default: all numeric)
        """
        if columns is None:
            columns = df.select_dtypes(include=['number']).columns.tolist()
        
        for col in columns:
            mean_val = df[col].mean()
            std_val = df[col].std()
            if std_val != 0:
                df[col] = (df[col] - mean_val) / std_val
        
        return df
    
    def _one_hot_encode(self, df: pd.DataFrame, columns: Union[str, List[str]],
                        **kwargs) -> pd.DataFrame:
        """
        One-hot encode categorical columns
        
        Args:
            columns: Column(s) to encode
        """
        if isinstance(columns, str):
            columns = [columns]
        
        return pd.get_dummies(df, columns=columns, drop_first=False)
    
    def _create_column(self, df: pd.DataFrame, name: str, 
                       expression: str, **kwargs) -> pd.DataFrame:
        """
        Create new column from expression
        
        Args:
            name: New column name
            expression: Expression to evaluate (e.g., "col1 + col2")
        """
        df[name] = df.eval(expression)
        return df
