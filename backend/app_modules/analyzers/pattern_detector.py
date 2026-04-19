"""
Pattern Detector for Vishleshak AI v1
Detects various patterns in datasets

Features:
- Trend patterns (increasing/decreasing/stable)
- Cyclical patterns
- Categorical distribution patterns
- Time-based patterns (if datetime present)
- Relationship patterns
- Data quality patterns
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')


class PatternDetector:
    """
    Advanced pattern detection engine
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize pattern detector
        
        Args:
            df: Pandas DataFrame to analyze
        """
        self.df = df.copy()
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    def detect_all_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect all types of patterns
        
        Returns:
            Dictionary with detected patterns by type
        """
        return {
            'trend_patterns': self._detect_trends(),
            'cyclical_patterns': self._detect_cyclical_patterns(),
            'categorical_patterns': self._detect_categorical_patterns(),
            'time_patterns': self._detect_time_patterns(),
            'relationship_patterns': self._detect_relationships(),
            'anomaly_patterns': self._detect_anomalies(),
            'data_quality_patterns': self._detect_data_quality_issues()
        }
    
    def _detect_trends(self) -> List[Dict[str, Any]]:
        """
        Detect trend patterns in numeric columns
        Uses linear regression to identify trends
        """
        trends = []
        
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            
            if len(data) < 3:
                continue
            
            # Create index for regression
            x = np.arange(len(data))
            y = data.values
            
            # Perform linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Determine trend type
            if p_value < 0.05:  # Significant trend
                if slope > 0:
                    trend_type = 'increasing'
                    trend_strength = 'strong' if abs(r_value) > 0.7 else 'moderate'
                elif slope < 0:
                    trend_type = 'decreasing'
                    trend_strength = 'strong' if abs(r_value) > 0.7 else 'moderate'
                else:
                    trend_type = 'stable'
                    trend_strength = 'n/a'
                
                trends.append({
                    'column': col,
                    'pattern_type': 'trend',
                    'trend': trend_type,
                    'strength': trend_strength,
                    'slope': float(slope),
                    'r_squared': float(r_value ** 2),
                    'p_value': float(p_value),
                    'interpretation': f"{col} shows a {trend_strength} {trend_type} trend (R²={r_value**2:.3f})"
                })
        
        return trends
    
    def _detect_cyclical_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect cyclical/repeating patterns in numeric columns
        Uses autocorrelation
        """
        patterns = []
        
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            
            if len(data) < 20:  # Need enough data for cycles
                continue
            
            try:
                # Calculate autocorrelation
                autocorr = []
                for lag in range(1, min(20, len(data) // 2)):
                    corr = data.autocorr(lag=lag)
                    if not np.isnan(corr):
                        autocorr.append((lag, corr))
                
                # Find significant autocorrelations
                for lag, corr in autocorr:
                    if abs(corr) > 0.5:  # Significant correlation
                        patterns.append({
                            'column': col,
                            'pattern_type': 'cyclical',
                            'cycle_length': lag,
                            'correlation': float(corr),
                            'interpretation': f"{col} shows cyclical pattern with period of {lag} observations (correlation={corr:.3f})"
                        })
                        break  # Only report first significant cycle
            
            except Exception:
                continue
        
        return patterns
    
    def _detect_categorical_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect patterns in categorical columns
        """
        patterns = []
        
        for col in self.categorical_cols:
            data = self.df[col].dropna()
            
            if len(data) == 0:
                continue
            
            value_counts = data.value_counts()
            total = len(data)
            
            # Pattern 1: Dominant category
            if len(value_counts) > 0:
                top_pct = value_counts.iloc[0] / total * 100
                
                if top_pct > 50:
                    patterns.append({
                        'column': col,
                        'pattern_type': 'dominant_category',
                        'category': str(value_counts.index[0]),
                        'percentage': float(top_pct),
                        'interpretation': f"{col} has dominant category '{value_counts.index[0]}' ({top_pct:.1f}% of data)"
                    })
            
            # Pattern 2: Even distribution
            if len(value_counts) >= 3:
                # Calculate coefficient of variation for counts
                cv = value_counts.std() / value_counts.mean()
                
                if cv < 0.3:  # Low variation = even distribution
                    patterns.append({
                        'column': col,
                        'pattern_type': 'even_distribution',
                        'n_categories': len(value_counts),
                        'cv': float(cv),
                        'interpretation': f"{col} shows even distribution across {len(value_counts)} categories"
                    })
            
            # Pattern 3: High cardinality
            if len(value_counts) > total * 0.5:  # More than 50% unique
                patterns.append({
                    'column': col,
                    'pattern_type': 'high_cardinality',
                    'unique_values': len(value_counts),
                    'unique_percentage': float(len(value_counts) / total * 100),
                    'interpretation': f"{col} has high cardinality ({len(value_counts)} unique values, {len(value_counts)/total*100:.1f}%)"
                })
        
        return patterns
    
    def _detect_time_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect patterns in datetime columns
        """
        patterns = []
        
        for col in self.datetime_cols:
            data = self.df[col].dropna()
            
            if len(data) < 2:
                continue
            
            # Find gaps in time series
            time_diffs = data.diff().dropna()
            
            if len(time_diffs) > 0:
                median_gap = time_diffs.median()
                max_gap = time_diffs.max()
                
                patterns.append({
                    'column': col,
                    'pattern_type': 'time_series',
                    'date_range': f"{data.min()} to {data.max()}",
                    'median_gap': str(median_gap),
                    'max_gap': str(max_gap),
                    'interpretation': f"{col} spans from {data.min()} to {data.max()}"
                })
        
        return patterns
    
    def _detect_relationships(self) -> List[Dict[str, Any]]:
        """
        Detect relationships between columns
        """
        patterns = []
        
        # Numeric-Numeric relationships (beyond correlation)
        for i, col1 in enumerate(self.numeric_cols):
            for col2 in self.numeric_cols[i+1:]:
                data = self.df[[col1, col2]].dropna()
                
                if len(data) < 10:
                    continue
                
                # Check for non-linear relationships
                try:
                    # Polynomial fit
                    x = data[col1].values
                    y = data[col2].values
                    
                    # Try quadratic
                    z = np.polyfit(x, y, 2)
                    p = np.poly1d(z)
                    y_pred = p(x)
                    
                    r2_linear = np.corrcoef(x, y)[0, 1] ** 2
                    r2_quad = 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - y.mean()) ** 2))
                    
                    if r2_quad > r2_linear + 0.1:  # Quadratic is significantly better
                        patterns.append({
                            'column_1': col1,
                            'column_2': col2,
                            'pattern_type': 'non_linear_relationship',
                            'r2_linear': float(r2_linear),
                            'r2_quadratic': float(r2_quad),
                            'interpretation': f"{col1} and {col2} show non-linear relationship (quadratic R²={r2_quad:.3f})"
                        })
                except:
                    continue
        
        return patterns
    
    def _detect_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect anomaly patterns (beyond simple outliers)
        """
        anomalies = []
        
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            
            if len(data) < 10:
                continue
            
            # Z-score method
            z_scores = np.abs(stats.zscore(data))
            anomaly_mask = z_scores > 3
            anomaly_count = anomaly_mask.sum()
            
            if anomaly_count > 0:
                anomalies.append({
                    'column': col,
                    'pattern_type': 'statistical_anomaly',
                    'count': int(anomaly_count),
                    'percentage': float(anomaly_count / len(data) * 100),
                    'interpretation': f"{col} has {anomaly_count} statistical anomalies (Z-score > 3)"
                })
            
            # Check for sudden jumps
            if len(data) > 2:
                diffs = data.diff().dropna()
                if len(diffs) > 0:
                    mean_diff = diffs.mean()
                    std_diff = diffs.std()
                    
                    large_jumps = np.abs(diffs) > (mean_diff + 3 * std_diff)
                    jump_count = large_jumps.sum()
                    
                    if jump_count > 0:
                        anomalies.append({
                            'column': col,
                            'pattern_type': 'sudden_jumps',
                            'count': int(jump_count),
                            'interpretation': f"{col} has {jump_count} sudden jumps in values"
                        })
        
        return anomalies
    
    def _detect_data_quality_issues(self) -> List[Dict[str, Any]]:
        """
        Detect data quality patterns/issues
        """
        issues = []
        
        # Missing data patterns
        missing_pct = (self.df.isnull().sum() / len(self.df) * 100)
        high_missing = missing_pct[missing_pct > 30]
        
        for col in high_missing.index:
            issues.append({
                'column': col,
                'issue_type': 'high_missing_data',
                'missing_percentage': float(missing_pct[col]),
                'severity': 'high' if missing_pct[col] > 50 else 'moderate',
                'interpretation': f"{col} has high missing data ({missing_pct[col]:.1f}%)"
            })
        
        # Duplicate rows
        dup_count = self.df.duplicated().sum()
        if dup_count > 0:
            issues.append({
                'issue_type': 'duplicate_rows',
                'count': int(dup_count),
                'percentage': float(dup_count / len(self.df) * 100),
                'severity': 'high' if dup_count / len(self.df) > 0.05 else 'low',
                'interpretation': f"Dataset has {dup_count} duplicate rows ({dup_count/len(self.df)*100:.1f}%)"
            })
        
        # Low variance columns
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            if len(data) > 0:
                cv = data.std() / data.mean() if data.mean() != 0 else 0
                if cv < 0.01:  # Very low variance
                    issues.append({
                        'column': col,
                        'issue_type': 'low_variance',
                        'cv': float(cv),
                        'interpretation': f"{col} has very low variance (CV={cv:.4f}), may not be informative"
                    })
        
        # Single value columns
        for col in self.df.columns:
            if self.df[col].nunique() == 1:
                issues.append({
                    'column': col,
                    'issue_type': 'single_value',
                    'value': str(self.df[col].iloc[0]),
                    'severity': 'high',
                    'interpretation': f"{col} has only one unique value, consider removing"
                })
        
        return issues
    
    def get_pattern_summary(self) -> str:
        """
        Get a text summary of all detected patterns
        """
        all_patterns = self.detect_all_patterns()
        
        summary_parts = []
        
        for pattern_type, patterns in all_patterns.items():
            if patterns:
                summary_parts.append(f"{pattern_type.replace('_', ' ').title()}: {len(patterns)} found")
        
        return " | ".join(summary_parts) if summary_parts else "No significant patterns detected"
