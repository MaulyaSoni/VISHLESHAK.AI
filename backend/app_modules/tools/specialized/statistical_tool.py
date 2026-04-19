"""Advanced statistical analysis tool"""
import json
from typing import Dict, Any
import pandas as pd
import numpy as np
from scipy import stats

class StatisticalAnalyzerTool:
    name = "statistical_analyzer"
    description = """Performs comprehensive statistical analysis on dataset columns.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self, column: str, tests: list = None) -> str:
        if column not in self.df.columns:
            return f"Error: Column '{column}' not found"
        data = self.df[column].dropna()
        if not pd.api.types.is_numeric_dtype(data):
            return f"Error: Column '{column}' is not numeric"
        results = {
            "column": column,
            "n": int(len(data)),
            "mean": float(data.mean()),
            "median": float(data.median()),
            "std": float(data.std()),
            "min": float(data.min()),
            "max": float(data.max()),
            "q25": float(data.quantile(0.25)),
            "q75": float(data.quantile(0.75)),
            "skewness": float(data.skew()),
            "kurtosis": float(data.kurtosis()),
        }
        if tests:
            if "normality" in tests:
                stat, p = stats.shapiro(data.sample(min(5000, len(data))))
                results["normality_test"] = {
                    "test": "Shapiro-Wilk",
                    "statistic": float(stat),
                    "p_value": float(p),
                    "is_normal": p > 0.05,
                }
            if "outliers" in tests:
                Q1, Q3 = data.quantile([0.25, 0.75])
                IQR = Q3 - Q1
                outliers = data[(data < Q1 - 1.5*IQR) | (data > Q3 + 1.5*IQR)]
                results["outliers"] = {
                    "count": int(len(outliers)),
                    "percentage": float(len(outliers) / len(data) * 100),
                    "values": outliers.tolist()[:10],
                }
        return json.dumps(results, indent=2)
