"""
Statistical Analyzer for FINBOT v4
Performs comprehensive statistical analysis on datasets

Features:
- 20+ metrics per numeric column
- Correlation analysis
- Outlier detection (IQR method)
- K-means clustering
- Distribution analysis
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')


class StatisticalAnalyzer:
    """
    Comprehensive statistical analysis engine
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with dataset
        
        Args:
            df: Pandas DataFrame to analyze
        """
        self.df = df.copy()
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    def analyze_all(self) -> Dict[str, Any]:
        """
        Perform all statistical analyses
        
        Returns:
            Dictionary with all analysis results
        """
        return {
            'basic_info': self._get_basic_info(),
            'numeric_analysis': self._analyze_numeric_columns(),
            'categorical_analysis': self._analyze_categorical_columns(),
            'correlation_analysis': self._analyze_correlations(),
            'outlier_analysis': self._detect_outliers(),
            'clustering_analysis': self._perform_clustering()
        }
    
    def _get_basic_info(self) -> Dict[str, Any]:
        """Get basic dataset information"""
        return {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'numeric_columns': len(self.numeric_cols),
            'categorical_columns': len(self.categorical_cols),
            'memory_usage_mb': self.df.memory_usage(deep=True).sum() / 1024**2,
            'missing_values': self.df.isnull().sum().sum(),
            'duplicate_rows': self.df.duplicated().sum()
        }
    
    def _analyze_numeric_columns(self) -> Dict[str, Dict[str, Any]]:
        """
        Comprehensive analysis of numeric columns
        Returns 20+ metrics per column
        """
        results = {}
        
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            
            if len(data) == 0:
                continue
            
            # Basic statistics
            analysis = {
                'count': int(len(data)),
                'missing': int(self.df[col].isnull().sum()),
                'missing_pct': float(self.df[col].isnull().sum() / len(self.df) * 100),
                
                # Central tendency
                'mean': float(data.mean()),
                'median': float(data.median()),
                'mode': float(data.mode()[0]) if len(data.mode()) > 0 else None,
                
                # Dispersion
                'std': float(data.std()),
                'variance': float(data.var()),
                'min': float(data.min()),
                'max': float(data.max()),
                'range': float(data.max() - data.min()),
                
                # Quartiles
                'q1': float(data.quantile(0.25)),
                'q2': float(data.quantile(0.50)),
                'q3': float(data.quantile(0.75)),
                'iqr': float(data.quantile(0.75) - data.quantile(0.25)),
                
                # Advanced metrics
                'skewness': float(data.skew()),
                'kurtosis': float(data.kurtosis()),
                'cv': float(data.std() / data.mean() * 100) if data.mean() != 0 else 0,
                
                # Distribution
                'unique_values': int(data.nunique()),
                'unique_pct': float(data.nunique() / len(data) * 100)
            }
            
            # Normality test (if enough samples)
            if len(data) >= 8:
                try:
                    stat, p_value = stats.shapiro(data.sample(min(5000, len(data))))
                    analysis['normality_p_value'] = float(p_value)
                    analysis['is_normal'] = p_value > 0.05
                except:
                    analysis['normality_p_value'] = None
                    analysis['is_normal'] = None
            
            results[col] = analysis
        
        return results
    
    def _analyze_categorical_columns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze categorical columns"""
        results = {}
        
        for col in self.categorical_cols:
            data = self.df[col].dropna()
            
            if len(data) == 0:
                continue
            
            value_counts = data.value_counts()
            
            analysis = {
                'count': int(len(data)),
                'missing': int(self.df[col].isnull().sum()),
                'missing_pct': float(self.df[col].isnull().sum() / len(self.df) * 100),
                'unique_values': int(data.nunique()),
                'most_common': str(value_counts.index[0]),
                'most_common_count': int(value_counts.iloc[0]),
                'most_common_pct': float(value_counts.iloc[0] / len(data) * 100),
                'top_5_values': value_counts.head(5).to_dict()
            }
            
            results[col] = analysis
        
        return results
    
    def _analyze_correlations(self) -> Dict[str, Any]:
        """
        Analyze correlations between numeric columns
        """
        if len(self.numeric_cols) < 2:
            return {
                'correlation_matrix': {},
                'strong_correlations': [],
                'summary': 'Not enough numeric columns for correlation analysis'
            }
        
        # Calculate correlation matrix
        corr_matrix = self.df[self.numeric_cols].corr()
        
        # Find strong correlations
        strong_correlations = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                
                if abs(corr_value) >= 0.5:  # Threshold for "strong"
                    strong_correlations.append({
                        'variable_1': col1,
                        'variable_2': col2,
                        'correlation': float(corr_value),
                        'strength': self._correlation_strength(abs(corr_value)),
                        'direction': 'positive' if corr_value > 0 else 'negative'
                    })
        
        # Sort by absolute correlation
        strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'strong_correlations': strong_correlations,
            'total_pairs': len(strong_correlations),
            'summary': f"Found {len(strong_correlations)} strong correlations"
        }
    
    def _correlation_strength(self, corr: float) -> str:
        """Classify correlation strength"""
        abs_corr = abs(corr)
        if abs_corr >= 0.9:
            return 'very strong'
        elif abs_corr >= 0.7:
            return 'strong'
        elif abs_corr >= 0.5:
            return 'moderate'
        elif abs_corr >= 0.3:
            return 'weak'
        else:
            return 'very weak'
    
    def _detect_outliers(self) -> Dict[str, Any]:
        """
        Detect outliers using IQR method
        """
        outliers = {}
        
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            
            if len(data) < 4:
                continue
            
            # IQR method
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_mask = (self.df[col] < lower_bound) | (self.df[col] > upper_bound)
            outlier_count = outlier_mask.sum()
            
            if outlier_count > 0:
                outliers[col] = {
                    'count': int(outlier_count),
                    'percentage': float(outlier_count / len(self.df) * 100),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                    'outlier_values': self.df[col][outlier_mask].tolist()[:10]  # First 10
                }
        
        return {
            'columns_with_outliers': list(outliers.keys()),
            'outlier_details': outliers,
            'total_columns_checked': len(self.numeric_cols),
            'summary': f"Found outliers in {len(outliers)} out of {len(self.numeric_cols)} numeric columns"
        }
    
    def _perform_clustering(self) -> Dict[str, Any]:
        """
        Perform K-means clustering on numeric data
        """
        if len(self.numeric_cols) < 2 or len(self.df) < 10:
            return {
                'clusters': None,
                'summary': 'Not enough data for clustering'
            }
        
        try:
            # Prepare data
            data = self.df[self.numeric_cols].dropna()
            
            if len(data) < 10:
                return {
                    'clusters': None,
                    'summary': 'Not enough complete rows for clustering'
                }
            
            # Standardize
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(data)
            
            # Determine optimal number of clusters (2-5)
            n_clusters = min(5, max(2, len(data) // 10))
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(scaled_data)
            
            # Analyze clusters
            cluster_info = []
            for i in range(n_clusters):
                cluster_mask = clusters == i
                cluster_size = cluster_mask.sum()
                
                cluster_info.append({
                    'cluster_id': i,
                    'size': int(cluster_size),
                    'percentage': float(cluster_size / len(data) * 100)
                })
            
            return {
                'n_clusters': n_clusters,
                'cluster_sizes': cluster_info,
                'inertia': float(kmeans.inertia_),
                'summary': f"Data grouped into {n_clusters} clusters"
            }
        
        except Exception as e:
            return {
                'clusters': None,
                'summary': f'Clustering failed: {str(e)}'
            }
    
    def get_summary_stats(self, column: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for a specific column"""
        if column in self.numeric_cols:
            return self._analyze_numeric_columns().get(column)
        elif column in self.categorical_cols:
            return self._analyze_categorical_columns().get(column)
        else:
            return None
