"""Find correlations between variables"""
import json
import pandas as pd
import numpy as np

class CorrelationFinderTool:
    name = "correlation_finder"
    description = """Finds correlations between numeric columns."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self, method: str = "pearson", min_correlation: float = 0.3, target: str = None) -> str:
        numeric_cols = self.df.select_dtypes(include='number').columns
        if len(numeric_cols) < 2:
            return "Error: Need at least 2 numeric columns"
        corr_matrix = self.df[numeric_cols].corr(method=method)
        if target:
            if target not in corr_matrix.columns:
                return f"Error: Target '{target}' not found"
            target_corrs = corr_matrix[target].sort_values(ascending=False)
            target_corrs = target_corrs[target_corrs.abs() >= min_correlation]
            target_corrs = target_corrs[target_corrs.index != target]
            results = {
                "target": target,
                "correlations": {col: float(val) for col, val in target_corrs.items()},
            }
        else:
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
            corr_pairs = corr_matrix.where(mask).stack().sort_values(ascending=False)
            corr_pairs = corr_pairs[corr_pairs.abs() >= min_correlation]
            results = {
                "method": method,
                "min_correlation": min_correlation,
                "top_correlations": [
                    {
                        "var1": pair[0],
                        "var2": pair[1],
                        "correlation": float(val),
                        "strength": "strong" if abs(val) > 0.7 else "moderate" if abs(val) > 0.4 else "weak",
                    }
                    for pair, val in corr_pairs.head(20).items()
                ],
            }
        return json.dumps(results, indent=2)
