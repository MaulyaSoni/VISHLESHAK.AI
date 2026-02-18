"""Report generator - creates simple PDF or Excel report"""
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd

class ReportGeneratorTool:
    name = "report_generator"
    description = "Generate PDF or Excel summary reports from data."

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self, summary: bool = True, format: str = "pdf") -> dict:
        if format == "pdf":
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=letter)
            c.drawString(50, 750, "Vishleshak Report")
            c.drawString(50, 730, f"Rows: {len(self.df)} Columns: {len(self.df.columns)}")
            c.showPage()
            c.save()
            buf.seek(0)
            return {"pdf_bytes": buf.getvalue()}
        elif format in ("xlsx", "excel"):
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                self.df.head(50).to_excel(writer, index=False, sheet_name="sample")
            out.seek(0)
            return {"excel_bytes": out.getvalue()}
        else:
            return {"error": "unsupported format"}
