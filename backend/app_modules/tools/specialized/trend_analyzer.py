"""Trend analyzer tool - simple trend detection and seasonality check"""
import json
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

class TrendAnalyzerTool:
    name = "trend_analyzer"
    description = "Detects trend and seasonality in a time series column."

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self, time_col: str, value_col: str, freq: str = None) -> str:
        if time_col not in self.df.columns or value_col not in self.df.columns:
            return json.dumps({"error": "Columns not found"})
        ts = self.df.set_index(time_col)[value_col].dropna()
        if len(ts) < 10:
            return json.dumps({"error": "Not enough points for trend detection"})
        try:
            res = seasonal_decompose(ts, period=seasonal_period(ts))
            out = {
                "trend_present": res.trend.dropna().std() > 0,
                "seasonal_strength": float(res.seasonal.std()),
            }
            return json.dumps(out)
        except Exception as e:
            return json.dumps({"error": str(e)})

def seasonal_period(series):
    # heuristic: if index is datetime, try weekly/monthly
    try:
        if hasattr(series.index, 'inferred_freq') and series.index.inferred_freq:
            return 12
    except Exception:
        pass
    return max(3, int(len(series) / 4))
