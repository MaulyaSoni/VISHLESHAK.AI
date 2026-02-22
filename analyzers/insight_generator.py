"""
Insight Generator for Vishleshak AI v1
Combines statistical analysis and pattern detection with AI to generate insights

Features:
- Combines statistical and pattern analysis
- AI-powered insight generation using LLM
- Claude-level prompts for high-quality insights
- Prioritized recommendations
- Executive summary generation
"""

import pandas as pd
from typing import Dict, List, Any
from .statistical_analyzer import StatisticalAnalyzer
from .pattern_detector import PatternDetector
from core.llm import get_analysis_llm
import json


class InsightGenerator:
    """
    Generates comprehensive AI-powered insights from data analysis
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize insight generator
        
        Args:
            df: Pandas DataFrame to analyze
        """
        self.df = df
        self.stats_analyzer = StatisticalAnalyzer(df)
        self.pattern_detector = PatternDetector(df)
        self.llm = get_analysis_llm()
    
    def generate_comprehensive_insights(self) -> Dict[str, Any]:
        """
        Generate complete analysis with AI insights
        
        Returns:
            Dictionary containing:
            - statistical_analysis: Raw statistical results
            - pattern_analysis: Detected patterns
            - ai_insights: AI-generated insights
            - recommendations: Prioritized recommendations
            - executive_summary: High-level summary
        """
        
        # Run analyses
        stats_results = self.stats_analyzer.analyze_all()
        pattern_results = self.pattern_detector.detect_all_patterns()
        
        # Generate AI insights
        ai_insights = self._generate_ai_insights(stats_results, pattern_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(stats_results, pattern_results)
        
        # Generate executive summary
        exec_summary = self._generate_executive_summary(stats_results, pattern_results, ai_insights)
        
        return {
            'statistical_analysis': stats_results,
            'pattern_analysis': pattern_results,
            'ai_insights': ai_insights,
            'recommendations': recommendations,
            'executive_summary': exec_summary
        }
    
    def _generate_ai_insights(self, stats: Dict, patterns: Dict) -> str:
        """
        Generate AI-powered insights using LLM
        Uses Claude-level prompts for high-quality analysis
        """
        
        # Prepare context for LLM
        context = self._prepare_analysis_context(stats, patterns)
        
        # Claude-level prompt
        prompt = f"""You are an expert data analyst with deep statistical knowledge. Analyze this dataset and provide professional insights.

## Dataset Overview
{context['overview']}

## Statistical Findings
{context['statistics']}

## Pattern Analysis
{context['patterns']}

## Your Task
Provide a comprehensive analysis that includes:

1. **Key Findings**: What are the 3-5 most important discoveries in this data? Be specific with numbers and percentages.

2. **Data Characteristics**: Describe the nature of this dataset. What does it represent? What are its strengths and limitations?

3. **Notable Patterns**: Explain any significant trends, correlations, or anomalies. Why are they important?

4. **Statistical Significance**: Highlight any statistically significant findings. What do the numbers really tell us?

5. **Insights**: What deeper insights can be drawn from this analysis? What story does the data tell?

**Requirements:**
- Be specific and precise with numbers
- Use professional language
- Focus on actionable insights
- Explain statistical concepts clearly
- Highlight both opportunities and concerns

**Format:** Use clear sections with markdown headers (###) and bullet points where appropriate.
"""
        
        try:
            # Generate insights using LLM
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        
        except Exception as e:
            return f"**AI Analysis Unavailable**: {str(e)}\n\nPlease review the statistical analysis and pattern detection results above."
    
    def _prepare_analysis_context(self, stats: Dict, patterns: Dict) -> Dict[str, str]:
        """
        Prepare context for LLM from analysis results
        """
        
        # Overview
        basic_info = stats['basic_info']
        overview = f"""
- Total Records: {basic_info['total_rows']:,}
- Total Columns: {basic_info['total_columns']}
- Numeric Columns: {basic_info['numeric_columns']}
- Categorical Columns: {basic_info['categorical_columns']}
- Missing Values: {basic_info['missing_values']:,} ({basic_info['missing_values']/basic_info['total_rows']/basic_info['total_columns']*100:.2f}%)
- Duplicate Rows: {basic_info['duplicate_rows']}
"""
        
        # Statistics highlights
        statistics = []
        
        if stats['numeric_analysis']:
            statistics.append("**Numeric Columns:**")
            for col, analysis in list(stats['numeric_analysis'].items())[:5]:  # Top 5
                statistics.append(f"- {col}: mean={analysis['mean']:.2f}, std={analysis['std']:.2f}, range=[{analysis['min']:.2f}, {analysis['max']:.2f}]")
        
        if stats['correlation_analysis']['strong_correlations']:
            statistics.append("\n**Strong Correlations:**")
            for corr in stats['correlation_analysis']['strong_correlations'][:5]:
                statistics.append(f"- {corr['variable_1']} ↔ {corr['variable_2']}: {corr['correlation']:.3f} ({corr['strength']})")
        
        if stats['outlier_analysis']['columns_with_outliers']:
            statistics.append("\n**Outliers Detected:**")
            for col in stats['outlier_analysis']['columns_with_outliers'][:5]:
                details = stats['outlier_analysis']['outlier_details'][col]
                statistics.append(f"- {col}: {details['count']} outliers ({details['percentage']:.1f}%)")
        
        # Pattern highlights
        pattern_list = []
        
        for pattern_type, pattern_data in patterns.items():
            if pattern_data and len(pattern_data) > 0:
                pattern_list.append(f"**{pattern_type.replace('_', ' ').title()}:**")
                for p in pattern_data[:3]:  # Top 3 of each type
                    if 'interpretation' in p:
                        pattern_list.append(f"- {p['interpretation']}")
        
        return {
            'overview': overview.strip(),
            'statistics': '\n'.join(statistics),
            'patterns': '\n'.join(pattern_list) if pattern_list else "No significant patterns detected."
        }
    
    def _generate_recommendations(self, stats: Dict, patterns: Dict) -> List[str]:
        """
        Generate prioritized recommendations based on findings
        """
        recommendations = []
        
        basic_info = stats['basic_info']
        
        # Data quality recommendations
        if basic_info['missing_values'] > 0:
            missing_pct = (basic_info['missing_values'] / (basic_info['total_rows'] * basic_info['total_columns'])) * 100
            if missing_pct > 10:
                recommendations.append(
                    f"**Address Missing Data**: {basic_info['missing_values']:,} missing values ({missing_pct:.1f}%). "
                    "Consider imputation strategies or investigate why data is missing."
                )
        
        if basic_info['duplicate_rows'] > 0:
            dup_pct = (basic_info['duplicate_rows'] / basic_info['total_rows']) * 100
            if dup_pct > 1:
                recommendations.append(
                    f"**Remove Duplicates**: Found {basic_info['duplicate_rows']} duplicate rows ({dup_pct:.1f}%). "
                    "Review and remove duplicates to ensure data integrity."
                )
        
        # Correlation recommendations
        if stats['correlation_analysis']['strong_correlations']:
            strong_corrs = stats['correlation_analysis']['strong_correlations']
            if len(strong_corrs) > 0:
                top_corr = strong_corrs[0]
                recommendations.append(
                    f"**Investigate Strong Correlations**: {top_corr['variable_1']} and {top_corr['variable_2']} "
                    f"show {top_corr['strength']} {top_corr['direction']} correlation ({top_corr['correlation']:.3f}). "
                    "This relationship may be important for modeling or business insights."
                )
        
        # Outlier recommendations
        outlier_cols = stats['outlier_analysis']['columns_with_outliers']
        if len(outlier_cols) > 0:
            recommendations.append(
                f"**Review Outliers**: {len(outlier_cols)} columns contain outliers. "
                "Verify if these are data errors or legitimate extreme values. Consider outlier treatment strategies."
            )
        
        # Pattern-based recommendations
        trend_patterns = patterns.get('trend_patterns', [])
        if trend_patterns:
            for trend in trend_patterns[:2]:  # Top 2 trends
                if trend['trend'] != 'stable':
                    recommendations.append(
                        f"**Monitor Trend**: {trend['column']} shows a {trend['strength']} {trend['trend']} trend. "
                        "Consider time-series forecasting or trend analysis."
                    )
        
        # Data quality issues
        quality_issues = patterns.get('data_quality_patterns', [])
        high_severity = [q for q in quality_issues if q.get('severity') == 'high']
        if high_severity:
            for issue in high_severity[:2]:
                recommendations.append(f"**Data Quality Alert**: {issue['interpretation']}")
        
        # Clustering recommendations
        if stats['clustering_analysis'].get('n_clusters'):
            n_clusters = stats['clustering_analysis']['n_clusters']
            recommendations.append(
                f"**Natural Groupings Found**: Data naturally clusters into {n_clusters} groups. "
                "Consider segmentation analysis or targeted strategies for each group."
            )
        
        # Default recommendation if none found
        if not recommendations:
            recommendations.append(
                "**Data Looks Good**: No major data quality issues detected. "
                "Proceed with your analysis or modeling objectives."
            )
        
        return recommendations[:8]  # Return top 8 recommendations
    
    def _generate_executive_summary(self, stats: Dict, patterns: Dict, insights: str) -> str:
        """
        Generate executive summary (2-3 sentences)
        """
        basic_info = stats['basic_info']
        
        # Count significant findings
        n_correlations = len(stats['correlation_analysis'].get('strong_correlations', []))
        n_outlier_cols = len(stats['outlier_analysis'].get('columns_with_outliers', []))
        n_patterns = sum(len(p) for p in patterns.values() if isinstance(p, list))
        
        summary = (
            f"Analyzed {basic_info['total_rows']:,} records across {basic_info['total_columns']} columns "
            f"({basic_info['numeric_columns']} numeric, {basic_info['categorical_columns']} categorical). "
        )
        
        findings = []
        if n_correlations > 0:
            findings.append(f"{n_correlations} strong correlations")
        if n_outlier_cols > 0:
            findings.append(f"outliers in {n_outlier_cols} columns")
        if n_patterns > 0:
            findings.append(f"{n_patterns} significant patterns")
        
        if findings:
            summary += f"Discovered {', '.join(findings)}. "
        
        # Data quality note
        if basic_info['missing_values'] > 0 or basic_info['duplicate_rows'] > 0:
            summary += "Some data quality issues require attention."
        else:
            summary += "Data quality is good overall."
        
        return summary
    
    def quick_insights(self) -> str:
        """
        Generate quick insights without full analysis (faster)
        """
        basic_info = self.stats_analyzer._get_basic_info()
        
        return f"""
**Quick Overview:**
- {basic_info['total_rows']:,} rows × {basic_info['total_columns']} columns
- {basic_info['numeric_columns']} numeric, {basic_info['categorical_columns']} categorical
- {basic_info['missing_values']:,} missing values
- {basic_info['duplicate_rows']} duplicates

Run full analysis for detailed insights and recommendations.
"""
