"""Detect anomalies and outliers"""
import json
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

class AnomalyDetectorTool:
    name = "anomaly_detector"
    description = """Detects anomalies and outliers in dataset."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self, columns: list = None, method: str = "isolation_forest", contamination: float = 0.1) -> str:
        if columns is None:
            columns = self.df.select_dtypes(include='number').columns.tolist()
        if not columns:
            return "Error: No numeric columns available"
        data = self.df[columns].dropna()
        if len(data) < 10:
            return "Error: Need at least 10 data points"
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data)
        if method == "isolation_forest":
            detector = IsolationForest(contamination=contamination, random_state=42)
            predictions = detector.fit_predict(data_scaled)
        else:
            return f"Error: Method '{method}' not supported"
        anomaly_indices = np.where(predictions == -1)[0]
        anomalies = data.iloc[anomaly_indices]
        scores = detector.score_samples(data_scaled)
        anomaly_scores = scores[anomaly_indices]
        results = {
            "method": method,
            "total_points": int(len(data)),
            "anomalies_found": int(len(anomalies)),
            "contamination": contamination,
            "anomaly_percentage": float(len(anomalies) / len(data) * 100),
            "top_anomalies": [
                {
                    "index": int(idx),
                    "score": float(score),
                    "values": {col: float(anomalies.iloc[i][col]) for col in columns},
                }
                for i, (idx, score) in enumerate(zip(anomaly_indices, anomaly_scores))
                if i < 10
            ],
        }
        return json.dumps(results, indent=2)
