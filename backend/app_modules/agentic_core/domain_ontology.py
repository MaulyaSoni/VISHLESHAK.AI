"""
Phase 2A — Domain Ontology
===========================
DomainContext dataclass + 12 DATASET_SIGNATURES for auto-detection.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DomainContext:
    sector: str                        # "insurance"|"banking"|"ecommerce"|"finance"|"general"
    sub_sector: str                    # "claims"|"health"|"motor"|"nbfc" …
    confidence: float                  # 0.0–1.0
    primary_kpis: List[str]            # top 5 to auto-compute
    analysis_template: str
    benchmarks: Dict[str, float]       # kpi_name → industry median
    regulatory_framework: str          # "IRDAI"|"RBI"|"SEBI"|"MCA"|"None"
    india_specific: bool
    auto_insights: List[str]           # 4 mandatory insight prompts
    column_warnings: List[str]         # data quality alerts for this domain


# ─────────────────────────────────────────────────────────────────────────────
#  12 DATASET SIGNATURES
# ─────────────────────────────────────────────────────────────────────────────

DATASET_SIGNATURES: Dict[str, dict] = {

    # ── 1. Insurance Claims ──────────────────────────────────────────────────
    "insurance_claims": {
        "required_columns":       ["claim", "premium", "policy"],
        "optional_columns":       ["loss", "incurred", "settled", "outstanding",
                                   "zone", "channel", "product"],
        "numeric_indicators":     ["claim_amount", "premium_amount", "sum_insured",
                                   "claims_paid", "net_premium"],
        "date_indicators":        ["claim_date", "policy_date", "settlement_date",
                                   "intimation_date"],
        "categorical_indicators": ["policy_type", "product_type", "zone", "channel"],
        "min_match_score":        0.45,
        "sector":                 "insurance",
        "sub_sector":             "claims",
        "primary_kpis":           ["loss_ratio", "claims_frequency", "settlement_ratio",
                                   "average_claim_size", "outstanding_claims_ratio"],
        "regulatory_framework":   "IRDAI",
        "benchmarks": {
            "loss_ratio":                0.68,
            "combined_ratio":            0.98,
            "claims_frequency":          0.032,
            "settlement_ratio":          0.87,
            "outstanding_claims_ratio":  0.13,
        },
        "auto_insights": [
            "What is the loss ratio vs IRDAI median of 68%?",
            "Which product types have highest claims frequency?",
            "Geographic zones with abnormal claim patterns?",
            "What % of claims are settled vs outstanding?",
        ],
        "india_specific": True,
    },

    # ── 2. Insurance Health ──────────────────────────────────────────────────
    "insurance_health": {
        "required_columns":       ["claim", "premium", "member", "hospital"],
        "optional_columns":       ["diagnosis", "procedure", "age", "gender",
                                   "network", "pre_existing"],
        "numeric_indicators":     ["claim_amount", "premium", "sum_insured",
                                   "copay", "deductible"],
        "date_indicators":        ["admission_date", "discharge_date", "claim_date"],
        "categorical_indicators": ["diagnosis_category", "hospital_type", "network_type"],
        "min_match_score":        0.45,
        "sector":                 "insurance",
        "sub_sector":             "health",
        "primary_kpis":           ["loss_ratio", "claims_frequency", "average_claim_size",
                                   "network_utilization", "readmission_rate"],
        "regulatory_framework":   "IRDAI",
        "benchmarks": {
            "loss_ratio":            0.72,
            "claims_frequency":      0.18,
            "network_utilization":   0.65,
        },
        "auto_insights": [
            "What is the health loss ratio vs IRDAI benchmark of 72%?",
            "Top 5 diagnosis categories by claim amount?",
            "Network vs non-network hospital utilization split?",
            "Age-band wise claims frequency analysis?",
        ],
        "india_specific": True,
    },

    # ── 3. Banking Financials ────────────────────────────────────────────────
    "banking_financials": {
        "required_columns":       ["interest", "income", "loan", "deposit"],
        "optional_columns":       ["npa", "provision", "capital", "tier1",
                                   "advances", "borrowing"],
        "numeric_indicators":     ["net_interest_income", "total_income", "gross_npa",
                                   "net_npa", "capital_adequacy", "advances"],
        "date_indicators":        ["quarter_end", "year_end", "reporting_date"],
        "categorical_indicators": ["bank_type", "segment", "product_category"],
        "min_match_score":        0.45,
        "sector":                 "banking",
        "sub_sector":             "financials",
        "primary_kpis":           ["nim", "gnpa_ratio", "nnpa_ratio", "car",
                                   "return_on_assets"],
        "regulatory_framework":   "RBI",
        "benchmarks": {
            "nim":              0.031,
            "gnpa_ratio":       0.038,
            "nnpa_ratio":       0.010,
            "car":              0.155,
            "return_on_assets": 0.012,
        },
        "auto_insights": [
            "What is the NIM vs RBI sector median of 3.1%?",
            "GNPA trend — improving or deteriorating?",
            "Capital Adequacy Ratio vs RBI minimum of 11.5%?",
            "Return on Assets vs peer benchmark of 1.2%?",
        ],
        "india_specific": True,
    },

    # ── 4. E-Commerce Orders ─────────────────────────────────────────────────
    "ecommerce_orders": {
        "required_columns":       ["order", "customer", "product"],
        "optional_columns":       ["sku", "category", "return", "refund",
                                   "discount", "coupon", "channel"],
        "numeric_indicators":     ["order_value", "order_amount", "quantity",
                                   "discount_amount", "revenue"],
        "date_indicators":        ["order_date", "delivery_date", "return_date"],
        "categorical_indicators": ["product_category", "channel", "payment_method",
                                   "city", "state"],
        "min_match_score":        0.45,
        "sector":                 "ecommerce",
        "sub_sector":             "orders",
        "primary_kpis":           ["average_order_value", "return_rate",
                                   "customer_repeat_rate", "discount_rate",
                                   "revenue_per_customer"],
        "regulatory_framework":   "None",
        "benchmarks": {
            "return_rate":          0.08,
            "average_order_value":  850.0,
            "customer_repeat_rate": 0.35,
            "discount_rate":        0.12,
        },
        "auto_insights": [
            "What is the return rate vs industry benchmark of 8%?",
            "Top 5 product categories by revenue contribution?",
            "Repeat customer rate and cohort retention trends?",
            "Discount rate impact on net revenue?",
        ],
        "india_specific": False,
    },

    # ── 5. Profit & Loss ─────────────────────────────────────────────────────
    "profit_loss": {
        "required_columns":       ["revenue", "expense", "profit"],
        "optional_columns":       ["ebitda", "depreciation", "tax", "interest",
                                   "gross_profit", "operating_profit"],
        "numeric_indicators":     ["total_revenue", "total_expense", "net_profit",
                                   "gross_margin", "operating_margin"],
        "date_indicators":        ["period", "quarter", "year", "month"],
        "categorical_indicators": ["segment", "business_unit", "geography"],
        "min_match_score":        0.45,
        "sector":                 "finance",
        "sub_sector":             "p_and_l",
        "primary_kpis":           ["pat_margin", "ebitda_margin", "gross_margin",
                                   "revenue_growth", "expense_ratio"],
        "regulatory_framework":   "MCA",
        "benchmarks": {
            "pat_margin":    0.082,
            "ebitda_margin": 0.18,
            "gross_margin":  0.35,
            "expense_ratio": 0.72,
        },
        "auto_insights": [
            "What is the PAT margin vs sector median of 8.2%?",
            "EBITDA margin trend over reporting periods?",
            "Top 3 expense heads as % of revenue?",
            "Revenue growth rate — accelerating or decelerating?",
        ],
        "india_specific": False,
    },

    # ── 6. HR Payroll ────────────────────────────────────────────────────────
    "hr_payroll": {
        "required_columns":       ["employee", "salary", "department"],
        "optional_columns":       ["designation", "grade", "ctc", "bonus",
                                   "pf", "esi", "leave", "attendance"],
        "numeric_indicators":     ["basic_salary", "gross_salary", "net_salary",
                                   "ctc", "bonus_amount", "pf_contribution"],
        "date_indicators":        ["joining_date", "payroll_date", "exit_date"],
        "categorical_indicators": ["department", "designation", "grade", "location"],
        "min_match_score":        0.45,
        "sector":                 "hr",
        "sub_sector":             "payroll",
        "primary_kpis":           ["average_ctc", "payroll_cost_ratio",
                                   "attrition_rate", "bonus_pct",
                                   "headcount_by_department"],
        "regulatory_framework":   "MCA",
        "benchmarks": {
            "attrition_rate":     0.18,
            "payroll_cost_ratio": 0.35,
            "bonus_pct":          0.12,
        },
        "auto_insights": [
            "What is the attrition rate vs industry benchmark of 18%?",
            "Department-wise payroll cost distribution?",
            "Grade-wise average CTC analysis?",
            "Bonus as % of CTC across departments?",
        ],
        "india_specific": True,
    },

    # ── 7. GST Transactions ──────────────────────────────────────────────────
    "gst_transactions": {
        "required_columns":       ["gstin", "invoice", "tax"],
        "optional_columns":       ["cgst", "sgst", "igst", "cess",
                                   "taxable_value", "hsn", "supplier"],
        "numeric_indicators":     ["taxable_amount", "cgst_amount", "sgst_amount",
                                   "igst_amount", "total_tax", "invoice_value"],
        "date_indicators":        ["invoice_date", "filing_date", "period"],
        "categorical_indicators": ["supply_type", "hsn_code", "state", "category"],
        "min_match_score":        0.50,
        "sector":                 "tax",
        "sub_sector":             "gst",
        "primary_kpis":           ["effective_tax_rate", "input_credit_utilization",
                                   "tax_liability", "compliance_rate",
                                   "average_invoice_value"],
        "regulatory_framework":   "MCA",
        "benchmarks": {
            "effective_tax_rate":        0.18,
            "input_credit_utilization":  0.85,
            "compliance_rate":           0.95,
        },
        "auto_insights": [
            "What is the effective GST rate vs standard rate of 18%?",
            "Input tax credit utilization efficiency?",
            "Top 5 HSN codes by tax liability?",
            "Month-wise GST filing compliance rate?",
        ],
        "india_specific": True,
    },

    # ── 8. Loan Portfolio ────────────────────────────────────────────────────
    "loan_portfolio": {
        "required_columns":       ["loan", "borrower", "emi"],
        "optional_columns":       ["principal", "interest_rate", "tenure",
                                   "outstanding", "overdue", "dpd", "npa"],
        "numeric_indicators":     ["loan_amount", "outstanding_principal",
                                   "emi_amount", "overdue_amount", "dpd_days"],
        "date_indicators":        ["disbursement_date", "due_date", "closure_date"],
        "categorical_indicators": ["loan_type", "product", "bucket", "state"],
        "min_match_score":        0.45,
        "sector":                 "banking",
        "sub_sector":             "loan_portfolio",
        "primary_kpis":           ["gnpa_ratio", "nnpa_ratio", "collection_efficiency",
                                   "par_30", "par_90"],
        "regulatory_framework":   "RBI",
        "benchmarks": {
            "gnpa_ratio":            0.038,
            "collection_efficiency": 0.96,
            "par_30":                0.04,
            "par_90":                0.02,
        },
        "auto_insights": [
            "What is the GNPA ratio vs RBI benchmark of 3.8%?",
            "Collection efficiency trend — improving or declining?",
            "PAR 30 and PAR 90 bucket analysis?",
            "Product-wise NPA concentration?",
        ],
        "india_specific": True,
    },

    # ── 9. Balance Sheet ─────────────────────────────────────────────────────
    "balance_sheet": {
        "required_columns":       ["asset", "liability", "equity"],
        "optional_columns":       ["current_asset", "fixed_asset", "current_liability",
                                   "long_term_debt", "retained_earnings", "capital"],
        "numeric_indicators":     ["total_assets", "total_liabilities", "shareholders_equity",
                                   "current_ratio", "debt_equity"],
        "date_indicators":        ["balance_date", "year_end", "quarter_end"],
        "categorical_indicators": ["asset_type", "liability_type", "segment"],
        "min_match_score":        0.45,
        "sector":                 "finance",
        "sub_sector":             "balance_sheet",
        "primary_kpis":           ["current_ratio", "debt_equity_ratio",
                                   "return_on_equity", "asset_turnover",
                                   "working_capital"],
        "regulatory_framework":   "MCA",
        "benchmarks": {
            "current_ratio":    1.5,
            "debt_equity_ratio": 1.0,
            "return_on_equity": 0.15,
            "asset_turnover":   0.8,
        },
        "auto_insights": [
            "What is the current ratio vs healthy benchmark of 1.5?",
            "Debt-equity ratio trend — leveraging or deleveraging?",
            "Return on equity vs sector median of 15%?",
            "Working capital adequacy analysis?",
        ],
        "india_specific": False,
    },

    # ── 10. NBFC Portfolio ───────────────────────────────────────────────────
    "nbfc_portfolio": {
        "required_columns":       ["loan", "nbfc", "borrower"],
        "optional_columns":       ["microfinance", "gold_loan", "vehicle_loan",
                                   "housing", "msme", "dpd", "npa"],
        "numeric_indicators":     ["aum", "disbursement", "collection",
                                   "npa_amount", "provision"],
        "date_indicators":        ["disbursement_date", "collection_date", "reporting_date"],
        "categorical_indicators": ["product_type", "segment", "geography", "bucket"],
        "min_match_score":        0.45,
        "sector":                 "banking",
        "sub_sector":             "nbfc",
        "primary_kpis":           ["gnpa_ratio", "collection_efficiency",
                                   "cost_of_funds", "nim", "par_30"],
        "regulatory_framework":   "RBI",
        "benchmarks": {
            "gnpa_ratio":            0.045,
            "collection_efficiency": 0.95,
            "cost_of_funds":         0.085,
            "nim":                   0.065,
        },
        "auto_insights": [
            "What is the GNPA ratio vs NBFC benchmark of 4.5%?",
            "Collection efficiency vs target of 95%?",
            "Cost of funds trend and NIM compression?",
            "Product-wise AUM and NPA concentration?",
        ],
        "india_specific": True,
    },

    # ── 11. Mutual Fund / Investment ─────────────────────────────────────────
    "investment_portfolio": {
        "required_columns":       ["fund", "nav", "return"],
        "optional_columns":       ["aum", "scheme", "category", "benchmark",
                                   "alpha", "beta", "sharpe", "expense_ratio"],
        "numeric_indicators":     ["nav", "aum", "return_1y", "return_3y",
                                   "alpha", "beta", "sharpe_ratio"],
        "date_indicators":        ["nav_date", "inception_date", "valuation_date"],
        "categorical_indicators": ["fund_category", "fund_house", "scheme_type"],
        "min_match_score":        0.45,
        "sector":                 "finance",
        "sub_sector":             "investment",
        "primary_kpis":           ["sharpe_ratio", "alpha", "beta",
                                   "expense_ratio", "return_vs_benchmark"],
        "regulatory_framework":   "SEBI",
        "benchmarks": {
            "sharpe_ratio":  1.0,
            "expense_ratio": 0.015,
            "alpha":         0.02,
        },
        "auto_insights": [
            "What is the Sharpe ratio vs benchmark of 1.0?",
            "Alpha generation vs category average?",
            "Expense ratio vs SEBI limit of 2.25%?",
            "1Y and 3Y return vs benchmark index?",
        ],
        "india_specific": True,
    },

    # ── 12. Sales / Revenue ──────────────────────────────────────────────────
    "sales_revenue": {
        "required_columns":       ["sales", "revenue", "product"],
        "optional_columns":       ["region", "salesperson", "target", "quota",
                                   "pipeline", "conversion", "lead"],
        "numeric_indicators":     ["sales_amount", "revenue", "target",
                                   "achievement_pct", "pipeline_value"],
        "date_indicators":        ["sale_date", "period", "quarter", "month"],
        "categorical_indicators": ["product", "region", "channel", "salesperson"],
        "min_match_score":        0.40,
        "sector":                 "finance",
        "sub_sector":             "sales",
        "primary_kpis":           ["revenue_growth", "target_achievement",
                                   "average_deal_size", "win_rate",
                                   "sales_per_rep"],
        "regulatory_framework":   "None",
        "benchmarks": {
            "target_achievement": 1.0,
            "win_rate":           0.25,
            "revenue_growth":     0.15,
        },
        "auto_insights": [
            "What is the target achievement rate vs 100%?",
            "Top 5 products / regions by revenue contribution?",
            "Win rate vs industry benchmark of 25%?",
            "Month-over-month revenue growth trend?",
        ],
        "india_specific": False,
    },
}
