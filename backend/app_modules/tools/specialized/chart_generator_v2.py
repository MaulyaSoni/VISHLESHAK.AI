"""Chart generator tool (simple matplotlib wrapper)"""
import io
import base64
import matplotlib.pyplot as plt
import pandas as pd

class ChartGeneratorTool:
    name = "chart_generator"
    description = "Generate charts from dataframe columns and return image bytes/base64."

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self, x: str = None, y: str = None, kind: str = "line") -> dict:
        if x and x not in self.df.columns:
            return {"error": f"Column {x} not found"}
        if y and y not in self.df.columns:
            return {"error": f"Column {y} not found"}
        fig, ax = plt.subplots(figsize=(6, 4))
        try:
            if kind == "line":
                if x and y:
                    self.df.plot(x=x, y=y, kind="line", ax=ax)
                elif y:
                    self.df[y].plot(ax=ax)
                else:
                    self.df.select_dtypes(include="number").iloc[:, 0].plot(ax=ax)
            elif kind == "hist":
                self.df[y].hist(ax=ax)
            elif kind == "bar":
                self.df.groupby(x)[y].mean().plot(kind="bar", ax=ax)
            else:
                self.df[y].plot(ax=ax)
            buf = io.BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format="png")
            plt.close(fig)
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode("utf-8")
            return {"image_base64": b64}
        except Exception as e:
            return {"error": str(e)}
