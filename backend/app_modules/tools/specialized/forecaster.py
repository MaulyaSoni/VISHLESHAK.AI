"""Simple forecaster wrapper using Prophet when available"""
import json
import pandas as pd
try:
    from prophet import Prophet
except Exception:
    Prophet = None

class ForecasterTool:
    name = "forecaster"
    description = "Forecast a univariate timeseries using Prophet or a simple moving average fallback."

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self, time_col: str, value_col: str, periods: int = 12) -> str:
        if time_col not in self.df.columns or value_col not in self.df.columns:
            return json.dumps({"error": "Columns not found"})
        df = self.df[[time_col, value_col]].dropna().rename(columns={time_col: 'ds', value_col: 'y'})
        if Prophet:
            m = Prophet()
            m.fit(df)
            future = m.make_future_dataframe(periods=periods)
            forecast = m.predict(future)
            res = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).to_dict(orient='records')
            return json.dumps(res, default=str)
        else:
            # fallback: simple moving average forecast
            vals = df['y'].values
            if len(vals) == 0:
                return json.dumps({"error": "No data"})
            ma = vals[-min(len(vals), 10):].mean()
            res = [{'period': i+1, 'forecast': float(ma)} for i in range(periods)]
            return json.dumps(res)
