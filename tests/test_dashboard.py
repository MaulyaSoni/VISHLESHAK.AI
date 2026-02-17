"""
Test script for Dashboard Visualizer
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from utils.dashboard_visualizer import DashboardVisualizer

def test_dashboard():
    """Test the dashboard visualizer with sample data"""
    
    # Create sample financial dataset
    np.random.seed(42)
    n_rows = 100
    
    df = pd.DataFrame({
        'Date': pd.date_range('2023-01-01', periods=n_rows),
        'Revenue': np.random.randint(1000, 50000, n_rows),
        'Expenses': np.random.randint(500, 30000, n_rows),
        'Profit': np.random.randint(-5000, 20000, n_rows),
        'Customer_Count': np.random.randint(10, 500, n_rows),
        'Category': np.random.choice(['A', 'B', 'C', 'D'], n_rows),
        'Region': np.random.choice(['North', 'South', 'East', 'West'], n_rows),
        'Product': np.random.choice(['Product1', 'Product2', 'Product3'], n_rows)
    })
    
    print("✅ Created sample dataset:")
    print(f"   - Rows: {len(df)}")
    print(f"   - Columns: {len(df.columns)}")
    print()
    
    # Initialize dashboard
    print("🔧 Initializing Dashboard Visualizer...")
    dashboard = DashboardVisualizer(df)
    print(f"   - Numeric columns: {len(dashboard.numeric_cols)}")
    print(f"   - Categorical columns: {len(dashboard.categorical_cols)}")
    print(f"   - Datetime columns: {len(dashboard.datetime_cols)}")
    print()
    
    # Generate summary metrics
    print("📊 Generating summary metrics...")
    metrics = dashboard.create_summary_metrics()
    print(f"   - Total rows: {metrics['total_rows']}")
    print(f"   - Total columns: {metrics['total_columns']}")
    print(f"   - Missing percentage: {metrics['missing_percentage']}%")
    print()
    
    # Generate dashboard charts
    print("🎨 Generating dashboard charts...")
    figures = dashboard.create_overview_dashboard()
    print(f"   - Generated {len(figures)} charts")
    for i, fig in enumerate(figures, 1):
        print(f"     {i}. {fig.layout.title.text}")
    print()
    
    # Test custom chart
    print("🎯 Testing custom chart creation...")
    custom_fig = dashboard.create_custom_chart(
        chart_type='scatter',
        x='Revenue',
        y='Profit',
        color='Category',
        title='Revenue vs Profit by Category'
    )
    if custom_fig:
        print(f"   ✅ Custom chart created: {custom_fig.layout.title.text}")
    print()
    
    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    test_dashboard()
