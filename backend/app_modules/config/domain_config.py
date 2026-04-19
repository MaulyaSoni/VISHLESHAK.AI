"""
Domain Intelligence Config
Switches behavior based on industry: Finance, Insurance, E-commerce, General
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


DOMAIN_CONFIGS = {
    "finance": {
        "name": "Finance",
        "focus_areas": [
            "Revenue trends and expense ratios",
            "Year-over-year comparisons",
            "Cash flow anomalies",
            "Risk concentration analysis",
            "Profitability metrics"
        ],
        "metrics": [
            "revenue", "profit", "loss", "income", "expense", "cost",
            "asset", "liability", "equity", "cash", "roi", "margin"
        ],
        "colors": {
            "primary": "#10B981",
            "secondary": "#059669",
            "accent": "#34D399"
        },
        "system_prompt_addition": """
Focus your analysis on financial metrics:
- Identify revenue trends and expense patterns
- Analyze year-over-year or period-over-period changes
- Flag any cash flow anomalies or liquidity concerns
- Assess risk concentration in portfolios or accounts
- Calculate profitability ratios and margins
"""
    },
    "insurance": {
        "name": "Insurance",
        "focus_areas": [
            "Loss ratio monitoring",
            "Claim frequency analysis",
            "Premium adequacy assessment",
            "Risk segmentation insights",
            "IRDAI compliance indicators"
        ],
        "metrics": [
            "claim", "premium", "policy", "coverage", "risk",
            "policyholder", "loss", "benefit", "deductible"
        ],
        "colors": {
            "primary": "#F59E0B",
            "secondary": "#D97706",
            "accent": "#FBBF24"
        },
        "system_prompt_addition": """
Focus your analysis on insurance metrics:
- Monitor loss ratios and claim frequencies
- Assess premium adequacy and pricing accuracy
- Analyze risk segmentation and segmentation drift
- Identify potential compliance concerns
- Evaluate policyholder behavior patterns
"""
    },
    "ecommerce": {
        "name": "E-Commerce",
        "focus_areas": [
            "Customer churn signals",
            "Basket size trends",
            "Return rate analysis",
            "Cohort retention patterns",
            "Seasonal demand patterns"
        ],
        "metrics": [
            "order", "customer", "cart", "churn", "basket",
            "return", "sku", "product", "revenue", "quantity"
        ],
        "colors": {
            "primary": "#6366F1",
            "secondary": "#4F46E5",
            "accent": "#818CF8"
        },
        "system_prompt_addition": """
Focus your analysis on e-commerce metrics:
- Identify customer churn signals and at-risk customers
- Analyze basket size and cross-sell opportunities
- Monitor return rates and product performance
- Track cohort retention and lifetime value
- Detect seasonal demand patterns and trends
"""
    },
    "general": {
        "name": "General",
        "focus_areas": [
            "Data quality assessment",
            "Descriptive statistics",
            "Correlation analysis",
            "Pattern detection",
            "Distribution analysis"
        ],
        "metrics": [],
        "colors": {
            "primary": "#06B6D4",
            "secondary": "#0891B2",
            "accent": "#22D3EE"
        },
        "system_prompt_addition": """
Provide general analytical insights:
- Assess data quality and completeness
- Generate descriptive statistics
- Identify correlations and relationships
- Detect patterns and anomalies
- Suggest areas for deeper investigation
"""
    }
}


def get_domain_config(domain: str) -> Dict[str, Any]:
    """Get configuration for a specific domain"""
    return DOMAIN_CONFIGS.get(domain.lower(), DOMAIN_CONFIGS["general"])


def detect_domain_from_columns(columns: list) -> str:
    """Auto-detect domain from column names"""
    if not columns:
        return "general"
    
    col_str = " ".join(columns).lower()
    
    domain_scores = {}
    
    for domain, config in DOMAIN_CONFIGS.items():
        if not config.get("metrics"):
            continue
        
        score = sum(1 for m in config["metrics"] if m in col_str)
        if score > 0:
            domain_scores[domain] = score
    
    if domain_scores:
        return max(domain_scores, key=domain_scores.get)
    
    return "general"


def get_domain_system_prompt(domain: str) -> str:
    """Get additional system prompt for domain"""
    config = get_domain_config(domain)
    return config.get("system_prompt_addition", "")


def get_domain_colors(domain: str) -> Dict[str, str]:
    """Get color scheme for domain"""
    config = get_domain_config(domain)
    return config.get("colors", DOMAIN_CONFIGS["general"]["colors"])


def get_domain_focus_areas(domain: str) -> list:
    """Get focus areas for domain"""
    config = get_domain_config(domain)
    return config.get("focus_areas", [])


class DomainIntelligence:
    """
    Domain Intelligence handler for Vishleshak AI
    """
    
    def __init__(self, domain: str = "general"):
        self.domain = domain.lower()
        self.config = get_domain_config(self.domain)
        logger.info(f"✅ Domain Intelligence initialized: {self.domain}")
    
    def get_system_prompt(self) -> str:
        return self.config.get("system_prompt_addition", "")
    
    def get_colors(self) -> Dict[str, str]:
        return self.config.get("colors", {})
    
    def get_focus_areas(self) -> list:
        return self.config.get("focus_areas", [])


_domain_instance = None

def get_domain_intelligence(domain: str = "general") -> DomainIntelligence:
    global _domain_instance
    if _domain_instance is None or _domain_instance.domain != domain.lower():
        _domain_instance = DomainIntelligence(domain)
    return _domain_instance