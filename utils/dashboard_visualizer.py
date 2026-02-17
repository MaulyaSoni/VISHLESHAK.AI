"""
Dashboard Visualizer for FINBOT v4
Creates comprehensive analytics dashboard with multiple chart types
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class DashboardVisualizer:
    """
    Create comprehensive analytics dashboards with multiple chart types
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize dashboard with data
        
        Args:
            df: DataFrame to visualize
        """
        self.df = df
        self.numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Detect datetime columns that might be strings
        for col in df.select_dtypes(include=['object']).columns:
            try:
                pd.to_datetime(df[col].head())
                self.datetime_cols.append(col)
            except:
                pass
    
    def create_overview_dashboard(self) -> List[go.Figure]:
        """
        Create a comprehensive overview dashboard with multiple charts
        
        Returns:
            List of Plotly figures
        """
        figures = []
        
        # 1. Distribution Charts for numeric columns
        if len(self.numeric_cols) > 0:
            dist_fig = self._create_distribution_charts()
            if dist_fig:
                figures.append(dist_fig)
        
        # 2. Correlation Heatmap
        if len(self.numeric_cols) >= 2:
            corr_fig = self._create_correlation_heatmap()
            if corr_fig:
                figures.append(corr_fig)
        
        # 3. Categorical Analysis
        if len(self.categorical_cols) > 0:
            cat_fig = self._create_categorical_charts()
            if cat_fig:
                figures.append(cat_fig)
        
        # 4. Time Series Analysis
        if len(self.datetime_cols) > 0 and len(self.numeric_cols) > 0:
            time_fig = self._create_time_series_chart()
            if time_fig:
                figures.append(time_fig)
        
        # 5. Box Plots for outlier detection
        if len(self.numeric_cols) > 0:
            box_fig = self._create_box_plots()
            if box_fig:
                figures.append(box_fig)
        
        # 6. Scatter Matrix for relationships
        if len(self.numeric_cols) >= 2:
            scatter_fig = self._create_scatter_relationships()
            if scatter_fig:
                figures.append(scatter_fig)
        
        return figures
    
    def _create_distribution_charts(self) -> Optional[go.Figure]:
        """Create distribution histograms for numeric columns"""
        try:
            # Limit to first 6 numeric columns for clarity
            cols_to_plot = self.numeric_cols[:6]
            
            # Calculate layout
            n_cols = min(3, len(cols_to_plot))
            n_rows = (len(cols_to_plot) + n_cols - 1) // n_cols
            
            fig = make_subplots(
                rows=n_rows,
                cols=n_cols,
                subplot_titles=[f"{col} Distribution" for col in cols_to_plot],
                vertical_spacing=0.12,
                horizontal_spacing=0.1
            )
            
            for idx, col in enumerate(cols_to_plot):
                row = idx // n_cols + 1
                col_pos = idx % n_cols + 1
                
                fig.add_trace(
                    go.Histogram(
                        x=self.df[col],
                        name=col,
                        marker_color='skyblue',
                        showlegend=False,
                        nbinsx=30
                    ),
                    row=row,
                    col=col_pos
                )
            
            fig.update_layout(
                title_text="📊 Distribution Analysis",
                title_font_size=20,
                height=300 * n_rows,
                showlegend=False,
                template="plotly_white"
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating distribution charts: {e}")
            return None
    
    def _create_correlation_heatmap(self) -> Optional[go.Figure]:
        """Create correlation heatmap"""
        try:
            # Calculate correlation matrix
            corr_matrix = self.df[self.numeric_cols].corr()
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmid=0,
                text=np.round(corr_matrix.values, 2),
                texttemplate='%{text}',
                textfont={"size": 10},
                colorbar=dict(title="Correlation")
            ))
            
            fig.update_layout(
                title="🔗 Correlation Heatmap",
                title_font_size=20,
                height=600,
                width=800,
                template="plotly_white",
                xaxis_title="Variables",
                yaxis_title="Variables"
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating correlation heatmap: {e}")
            return None
    
    def _create_categorical_charts(self) -> Optional[go.Figure]:
        """Create bar charts for categorical columns"""
        try:
            # Limit to first 4 categorical columns
            cols_to_plot = self.categorical_cols[:4]
            
            # Calculate layout
            n_cols = min(2, len(cols_to_plot))
            n_rows = (len(cols_to_plot) + n_cols - 1) // n_cols
            
            fig = make_subplots(
                rows=n_rows,
                cols=n_cols,
                subplot_titles=[f"{col} Distribution" for col in cols_to_plot],
                specs=[[{"type": "bar"}] * n_cols for _ in range(n_rows)],
                vertical_spacing=0.15,
                horizontal_spacing=0.15
            )
            
            colors = px.colors.qualitative.Set2
            
            for idx, col in enumerate(cols_to_plot):
                row = idx // n_cols + 1
                col_pos = idx % n_cols + 1
                
                # Get value counts
                value_counts = self.df[col].value_counts().head(10)
                
                fig.add_trace(
                    go.Bar(
                        x=value_counts.index.astype(str),
                        y=value_counts.values,
                        name=col,
                        marker_color=colors[idx % len(colors)],
                        showlegend=False
                    ),
                    row=row,
                    col=col_pos
                )
            
            fig.update_layout(
                title_text="📑 Categorical Analysis",
                title_font_size=20,
                height=400 * n_rows,
                showlegend=False,
                template="plotly_white"
            )
            
            fig.update_xaxes(tickangle=-45)
            
            return fig
        except Exception as e:
            logger.error(f"Error creating categorical charts: {e}")
            return None
    
    def _create_time_series_chart(self) -> Optional[go.Figure]:
        """Create time series line chart"""
        try:
            # Use first datetime column
            time_col = self.datetime_cols[0]
            
            # Convert to datetime if needed
            if self.df[time_col].dtype == 'object':
                df_copy = self.df.copy()
                df_copy[time_col] = pd.to_datetime(df_copy[time_col])
            else:
                df_copy = self.df
            
            # Sort by time
            df_copy = df_copy.sort_values(time_col)
            
            # Select up to 3 numeric columns for plotting
            numeric_to_plot = self.numeric_cols[:3]
            
            fig = go.Figure()
            
            colors = px.colors.qualitative.Bold
            
            for idx, col in enumerate(numeric_to_plot):
                fig.add_trace(go.Scatter(
                    x=df_copy[time_col],
                    y=df_copy[col],
                    mode='lines+markers',
                    name=col,
                    line=dict(color=colors[idx % len(colors)], width=2),
                    marker=dict(size=4)
                ))
            
            fig.update_layout(
                title="📈 Time Series Analysis",
                title_font_size=20,
                xaxis_title=time_col,
                yaxis_title="Value",
                height=500,
                template="plotly_white",
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating time series chart: {e}")
            return None
    
    def _create_box_plots(self) -> Optional[go.Figure]:
        """Create box plots for outlier detection"""
        try:
            # Limit to first 6 numeric columns
            cols_to_plot = self.numeric_cols[:6]
            
            fig = go.Figure()
            
            colors = px.colors.qualitative.Pastel
            
            for idx, col in enumerate(cols_to_plot):
                fig.add_trace(go.Box(
                    y=self.df[col],
                    name=col,
                    marker_color=colors[idx % len(colors)],
                    boxmean='sd'  # Show mean and standard deviation
                ))
            
            fig.update_layout(
                title="📦 Box Plot Analysis - Outlier Detection",
                title_font_size=20,
                yaxis_title="Value",
                height=500,
                template="plotly_white",
                showlegend=True
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating box plots: {e}")
            return None
    
    def _create_scatter_relationships(self) -> Optional[go.Figure]:
        """Create scatter plots showing relationships"""
        try:
            # Select top numeric columns (up to 4)
            cols_to_plot = self.numeric_cols[:4]
            
            if len(cols_to_plot) < 2:
                return None
            
            # Create scatter matrix
            fig = px.scatter_matrix(
                self.df,
                dimensions=cols_to_plot,
                title="🔍 Scatter Matrix - Variable Relationships",
                height=800,
                opacity=0.6
            )
            
            fig.update_layout(
                title_font_size=20,
                template="plotly_white"
            )
            
            fig.update_traces(diagonal_visible=False, marker=dict(size=3))
            
            return fig
        except Exception as e:
            logger.error(f"Error creating scatter relationships: {e}")
            return None
    
    def create_summary_metrics(self) -> Dict[str, Any]:
        """
        Create summary metrics for the dashboard
        
        Returns:
            Dictionary with key metrics
        """
        metrics = {
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "numeric_columns": len(self.numeric_cols),
            "categorical_columns": len(self.categorical_cols),
            "missing_values": int(self.df.isnull().sum().sum()),
            "missing_percentage": round((self.df.isnull().sum().sum() / (self.df.shape[0] * self.df.shape[1])) * 100, 2),
            "memory_usage_mb": round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
        
        # Add numeric summaries
        if len(self.numeric_cols) > 0:
            metrics["numeric_stats"] = {}
            for col in self.numeric_cols[:5]:  # Top 5 numeric columns
                metrics["numeric_stats"][col] = {
                    "mean": round(self.df[col].mean(), 2),
                    "median": round(self.df[col].median(), 2),
                    "std": round(self.df[col].std(), 2),
                    "min": round(self.df[col].min(), 2),
                    "max": round(self.df[col].max(), 2)
                }
        
        return metrics
    
    def create_custom_chart(
        self,
        chart_type: str,
        x: Optional[str] = None,
        y: Optional[str] = None,
        color: Optional[str] = None,
        title: Optional[str] = None
    ) -> Optional[go.Figure]:
        """
        Create a custom chart based on specifications
        
        Args:
            chart_type: Type of chart (bar, line, scatter, pie, etc.)
            x: Column for x-axis
            y: Column for y-axis
            color: Column for color coding
            title: Chart title
        
        Returns:
            Plotly Figure
        """
        try:
            if chart_type == "bar":
                fig = px.bar(self.df, x=x, y=y, color=color, title=title)
            elif chart_type == "line":
                fig = px.line(self.df, x=x, y=y, color=color, title=title)
            elif chart_type == "scatter":
                fig = px.scatter(self.df, x=x, y=y, color=color, title=title)
            elif chart_type == "pie":
                fig = px.pie(self.df, names=x, values=y, title=title)
            elif chart_type == "histogram":
                fig = px.histogram(self.df, x=x, color=color, title=title)
            else:
                logger.warning(f"Unsupported chart type: {chart_type}")
                return None
            
            fig.update_layout(
                template="plotly_white",
                height=500
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating custom chart: {e}")
            return None
