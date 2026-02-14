"""
Chart Generator Tool for FINBOT v4
Generates interactive Plotly visualizations
"""

from typing import Any, Dict, Optional, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
from tools.custom_tools.base_tool import BaseTool
from config import tool_config

logger = logging.getLogger(__name__)


class ChartGeneratorTool(BaseTool):
    """
    Generate interactive charts using Plotly
    
    Supported chart types:
    - scatter, line, bar, histogram
    - box, violin, pie, heatmap
    
    Usage:
        tool = ChartGeneratorTool()
        fig = tool.run(
            df=dataframe,
            chart_type="scatter",
            x="attendance",
            y="grades"
        )
    """
    
    def __init__(self):
        super().__init__(
            name="chart_generator",
            description=(
                "Generate interactive visualizations from data. "
                "Supports scatter plots, line charts, bar charts, histograms, "
                "box plots, violin plots, pie charts, and heatmaps. "
                "Input should specify chart type and column names. "
                "Returns an interactive Plotly figure."
            ),
            category="visualization"
        )
        self.width = tool_config.DEFAULT_CHART_WIDTH
        self.height = tool_config.DEFAULT_CHART_HEIGHT
        self.theme = tool_config.DEFAULT_CHART_THEME
    
    def run(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x: Optional[str] = None,
        y: Optional[str] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> go.Figure:
        """
        Generate a chart
        
        Args:
            df: DataFrame with data
            chart_type: Type of chart (scatter, line, bar, etc.)
            x: Column name for x-axis
            y: Column name for y-axis
            color: Column name for color coding
            size: Column name for size (scatter plots)
            title: Chart title
            **kwargs: Additional Plotly arguments
            
        Returns:
            Plotly Figure object
        """
        if not tool_config.ENABLE_VISUALIZATION:
            raise ValueError("Visualization is disabled")
        
        chart_type = chart_type.lower().strip()
        
        try:
            # Route to appropriate chart function
            if chart_type == "scatter":
                fig = self._create_scatter(df, x, y, color, size, title, **kwargs)
            
            elif chart_type == "line":
                fig = self._create_line(df, x, y, color, title, **kwargs)
            
            elif chart_type == "bar":
                fig = self._create_bar(df, x, y, color, title, **kwargs)
            
            elif chart_type == "histogram":
                fig = self._create_histogram(df, x, color, title, **kwargs)
            
            elif chart_type == "box":
                fig = self._create_box(df, x, y, color, title, **kwargs)
            
            elif chart_type == "violin":
                fig = self._create_violin(df, x, y, color, title, **kwargs)
            
            elif chart_type == "pie":
                fig = self._create_pie(df, x, y, title, **kwargs)
            
            elif chart_type == "heatmap":
                fig = self._create_heatmap(df, title, **kwargs)
            
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            # Apply common styling
            fig.update_layout(
                width=self.width,
                height=self.height,
                template=self.theme,
                title=title or f"{chart_type.title()} Chart"
            )
            
            logger.info(f"Generated {chart_type} chart")
            return fig
        
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            raise
    
    def _create_scatter(self, df, x, y, color, size, title, **kwargs):
        """Create scatter plot"""
        return px.scatter(
            df, x=x, y=y, color=color, size=size,
            title=title, **kwargs
        )
    
    def _create_line(self, df, x, y, color, title, **kwargs):
        """Create line chart"""
        return px.line(
            df, x=x, y=y, color=color,
            title=title, **kwargs
        )
    
    def _create_bar(self, df, x, y, color, title, **kwargs):
        """Create bar chart"""
        return px.bar(
            df, x=x, y=y, color=color,
            title=title, **kwargs
        )
    
    def _create_histogram(self, df, x, color, title, **kwargs):
        """Create histogram"""
        return px.histogram(
            df, x=x, color=color,
            title=title, **kwargs
        )
    
    def _create_box(self, df, x, y, color, title, **kwargs):
        """Create box plot"""
        return px.box(
            df, x=x, y=y, color=color,
            title=title, **kwargs
        )
    
    def _create_violin(self, df, x, y, color, title, **kwargs):
        """Create violin plot"""
        return px.violin(
            df, x=x, y=y, color=color,
            title=title, **kwargs
        )
    
    def _create_pie(self, df, names, values, title, **kwargs):
        """Create pie chart"""
        return px.pie(
            df, names=names, values=values,
            title=title, **kwargs
        )
    
    def _create_heatmap(self, df, title, **kwargs):
        """Create correlation heatmap"""
        # Calculate correlation matrix
        corr = df.select_dtypes(include=['number']).corr()
        
        return px.imshow(
            corr,
            text_auto=True,
            aspect="auto",
            title=title or "Correlation Heatmap",
            **kwargs
        )
    
    def auto_detect_chart_type(
        self,
        df: pd.DataFrame,
        x: str,
        y: Optional[str] = None
    ) -> str:
        """
        Auto-detect best chart type for given columns
        
        Args:
            df: DataFrame
            x: X-axis column
            y: Optional Y-axis column
            
        Returns:
            Suggested chart type
        """
        x_dtype = df[x].dtype
        
        if y is None:
            # Single column
            if pd.api.types.is_numeric_dtype(x_dtype):
                return "histogram"
            else:
                return "bar"  # Count plot
        
        y_dtype = df[y].dtype
        
        # Two columns
        if pd.api.types.is_numeric_dtype(x_dtype) and pd.api.types.is_numeric_dtype(y_dtype):
            return "scatter"
        
        elif pd.api.types.is_numeric_dtype(y_dtype):
            return "bar"
        
        else:
            return "bar"
