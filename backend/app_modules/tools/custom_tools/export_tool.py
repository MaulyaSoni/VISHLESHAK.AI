"""
Export Tool for Vishleshak AI v1
Exports data and results to various formats
"""

from typing import Any, Dict, Optional, Union
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
from tools.custom_tools.base_tool import BaseTool
from config import tool_config
import json

logger = logging.getLogger(__name__)


class ExportTool(BaseTool):
    """
    Export data to various formats
    
    Supported formats:
    - Excel (.xlsx)
    - CSV (.csv)
    - JSON (.json)
    - PDF (.pdf)
    - HTML (.html)
    
    Usage:
        tool = ExportTool()
        filepath = tool.run(
            data=dataframe,
            format="xlsx",
            filename="results"
        )
    """
    
    def __init__(self):
        super().__init__(
            name="export",
            description=(
                "Export data and analysis results to files. "
                "Supports Excel (xlsx), CSV, JSON, PDF, and HTML formats. "
                "Automatically handles large datasets and adds timestamps. "
                "Returns the filepath of the exported file."
            ),
            category="data"
        )
        self.export_dir = tool_config.EXPORT_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.max_rows = tool_config.MAX_EXPORT_ROWS
    
    def run(
        self,
        data: Union[pd.DataFrame, Dict, str],
        format: str = "xlsx",
        filename: Optional[str] = None,
        include_timestamp: bool = True,
        **kwargs
    ) -> str:
        """
        Export data to file
        
        Args:
            data: Data to export (DataFrame, dict, or string)
            format: Export format (xlsx, csv, json, pdf, html)
            filename: Optional filename (generated if not provided)
            include_timestamp: Add timestamp to filename
            **kwargs: Format-specific options
            
        Returns:
            Path to exported file
        """
        if not tool_config.ENABLE_EXPORT:
            raise ValueError("Export is disabled")
        
        format = format.lower().strip()
        
        # Generate filename if not provided
        if filename is None:
            filename = f"Vishleshak AI v1_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add timestamp if requested
        elif include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{filename}_{timestamp}"
        
        # Route to appropriate exporter
        try:
            if format == "xlsx":
                filepath = self._export_excel(data, filename, **kwargs)
            
            elif format == "csv":
                filepath = self._export_csv(data, filename, **kwargs)
            
            elif format == "json":
                filepath = self._export_json(data, filename, **kwargs)
            
            elif format == "pdf":
                filepath = self._export_pdf(data, filename, **kwargs)
            
            elif format == "html":
                filepath = self._export_html(data, filename, **kwargs)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Exported to: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise
    
    def _export_excel(self, data: pd.DataFrame, filename: str, **kwargs) -> Path:
        """Export to Excel"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Excel export requires DataFrame")
        
        # Check size
        if len(data) > self.max_rows:
            logger.warning(f"Dataset large ({len(data)} rows), may be slow")
        
        filepath = self.export_dir / f"{filename}.xlsx"
        
        # Export with formatting
        with pd.ExcelWriter(
            filepath,
            engine=tool_config.EXCEL_ENGINE
        ) as writer:
            data.to_excel(
                writer,
                sheet_name="Data",
                index=tool_config.EXCEL_INCLUDE_INDEX,
                freeze_panes=(1, 0) if tool_config.EXCEL_FREEZE_HEADER else None
            )
        
        return filepath
    
    def _export_csv(self, data: pd.DataFrame, filename: str, **kwargs) -> Path:
        """Export to CSV"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("CSV export requires DataFrame")
        
        filepath = self.export_dir / f"{filename}.csv"
        
        data.to_csv(
            filepath,
            index=False,
            encoding='utf-8'
        )
        
        return filepath
    
    def _export_json(self, data: Union[pd.DataFrame, Dict], 
                     filename: str, **kwargs) -> Path:
        """Export to JSON"""
        filepath = self.export_dir / f"{filename}.json"
        
        if isinstance(data, pd.DataFrame):
            data_dict = data.to_dict(orient='records')
        elif isinstance(data, dict):
            data_dict = data
        else:
            raise ValueError("JSON export requires DataFrame or dict")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _export_pdf(self, data: Union[pd.DataFrame, str], 
                    filename: str, **kwargs) -> Path:
        """Export to PDF"""
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        filepath = self.export_dir / f"{filename}.pdf"
        
        # Determine page size
        pagesize = letter if tool_config.PDF_PAGE_SIZE == "Letter" else A4
        
        doc = SimpleDocTemplate(str(filepath), pagesize=pagesize)
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title
        title = Paragraph(f"<b>{filename}</b>", styles['Title'])
        elements.append(title)
        
        # Add data
        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to table
            table_data = [data.columns.tolist()] + data.head(100).values.tolist()
            t = Table(table_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(t)
        
        elif isinstance(data, str):
            # Add text
            text = Paragraph(data, styles['Normal'])
            elements.append(text)
        
        doc.build(elements)
        return filepath
    
    def _export_html(self, data: Union[pd.DataFrame, str], 
                     filename: str, **kwargs) -> Path:
        """Export to HTML"""
        filepath = self.export_dir / f"{filename}.html"
        
        if isinstance(data, pd.DataFrame):
            # Export DataFrame as styled HTML table
            html = data.to_html(
                index=False,
                classes='table table-striped',
                border=0
            )
            
            # Wrap in complete HTML
            full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{filename}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th {{ background-color: #4CAF50; color: white; padding: 12px; text-align: left; }}
        td {{ border: 1px solid #ddd; padding: 8px; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>{filename}</h1>
    {html}
</body>
</html>
"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_html)
        
        elif isinstance(data, str):
            # Write string as HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data)
        
        return filepath
