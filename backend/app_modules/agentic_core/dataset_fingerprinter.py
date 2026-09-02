"""
Phase 2A — Dataset Fingerprinter
==================================
3-signal scoring algorithm to auto-detect dataset domain from column names,
value distributions, and naming patterns.

Signals:
  Signal 1 — Column name matching   (40%)
  Signal 2 — Value distribution     (35%)
  Signal 3 — Pattern matching       (25%)
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .domain_ontology import DATASET_SIGNATURES, DomainContext

logger = logging.getLogger("vishleshak.fingerprinter")


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalise(name: str) -> str:
    """Lowercase, strip spaces, replace separators with underscore."""
    return re.sub(r"[\s\-\.]+", "_", name.strip().lower())


def _partial_match(keyword: str, columns: List[str]) -> bool:
    """Return True if keyword appears as a substring in any column name."""
    kw = _normalise(keyword)
    for col in columns:
        if kw in _normalise(col):
            return True
    return False


def _count_matches(keywords: List[str], columns: List[str]) -> int:
    return sum(1 for kw in keywords if _partial_match(kw, columns))


# ─────────────────────────────────────────────────────────────────────────────
#  Signal 1 — Column name matching (40%)
# ─────────────────────────────────────────────────────────────────────────────

def _signal_column_match(sig: dict, columns: List[str]) -> float:
    """
    Score based on how many required + optional + indicator keywords
    appear in the uploaded column names.
    """
    required   = sig.get("required_columns", [])
    optional   = sig.get("optional_columns", [])
    numeric_i  = sig.get("numeric_indicators", [])
    date_i     = sig.get("date_indicators", [])
    cat_i      = sig.get("categorical_indicators", [])

    all_keywords = required + optional + numeric_i + date_i + cat_i
    if not all_keywords:
        return 0.0

    # Required columns carry extra weight
    req_hits = _count_matches(required, columns)
    req_score = req_hits / max(len(required), 1)

    # Optional + indicators
    opt_all = optional + numeric_i + date_i + cat_i
    opt_hits = _count_matches(opt_all, columns)
    opt_score = opt_hits / max(len(opt_all), 1) if opt_all else 0.0

    # Weighted: required 60%, optional 40%
    return round(0.60 * req_score + 0.40 * opt_score, 4)


# ─────────────────────────────────────────────────────────────────────────────
#  Signal 2 — Value distribution sanity check (35%)
# ─────────────────────────────────────────────────────────────────────────────

_DOMAIN_RANGE_HINTS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "insurance": {
        "loss_ratio":    (0.0, 2.0),
        "premium":       (100.0, 1e8),
        "claim":         (0.0, 1e8),
        "sum_insured":   (1000.0, 1e9),
    },
    "banking": {
        "nim":           (0.0, 0.20),
        "npa":           (0.0, 0.50),
        "advances":      (1e4, 1e12),
        "deposit":       (1e4, 1e12),
    },
    "ecommerce": {
        "order_value":   (1.0, 1e6),
        "quantity":      (1.0, 1e5),
        "discount":      (0.0, 1.0),
    },
    "finance": {
        "revenue":       (0.0, 1e12),
        "profit":        (-1e12, 1e12),
        "margin":        (-1.0, 1.0),
    },
}


def _signal_value_distribution(sig: dict, df: pd.DataFrame) -> float:
    """
    Check if numeric columns have values in plausible ranges for the domain.
    Returns fraction of matched range checks.
    """
    sector = sig.get("sector", "general")
    hints  = _DOMAIN_RANGE_HINTS.get(sector, {})
    if not hints:
        return 0.5  # neutral score for unknown domains

    checks_passed = 0
    checks_total  = 0

    for hint_kw, (lo, hi) in hints.items():
        for col in df.columns:
            if hint_kw in _normalise(col):
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_min = df[col].min()
                    col_max = df[col].max()
                    if lo <= col_min and col_max <= hi * 10:  # generous upper bound
                        checks_passed += 1
                    checks_total += 1
                break  # one column per hint

    if checks_total == 0:
        return 0.4  # slight penalty — no numeric columns matched hints
    return round(checks_passed / checks_total, 4)


# ─────────────────────────────────────────────────────────────────────────────
#  Signal 3 — Pattern matching (25%)
# ─────────────────────────────────────────────────────────────────────────────

_SUFFIX_PATTERNS = {
    "insurance": [r"_ratio$", r"_premium$", r"_claim$", r"_policy$", r"_incurred$"],
    "banking":   [r"_npa$", r"_advances$", r"_deposit$", r"_income$", r"_provision$"],
    "ecommerce": [r"_order$", r"_cart$", r"_sku$", r"_return$", r"_basket$"],
    "finance":   [r"_revenue$", r"_profit$", r"_expense$", r"_margin$", r"_ebitda$"],
    "hr":        [r"_salary$", r"_ctc$", r"_bonus$", r"_leave$", r"_grade$"],
    "tax":       [r"_gst$", r"_cgst$", r"_sgst$", r"_igst$", r"_hsn$"],
}

_GENERIC_PATTERNS = [r"_amount$", r"_date$", r"_id$", r"_code$", r"_type$", r"_name$"]


def _signal_pattern_match(sig: dict, columns: List[str]) -> float:
    """
    Check how many columns end with domain-specific suffixes.
    """
    sector   = sig.get("sector", "general")
    patterns = _SUFFIX_PATTERNS.get(sector, [])
    if not patterns:
        return 0.3

    norm_cols = [_normalise(c) for c in columns]
    hits = 0
    for col in norm_cols:
        for pat in patterns:
            if re.search(pat, col):
                hits += 1
                break

    # Normalise by number of columns (cap at 1.0)
    score = min(hits / max(len(columns), 1) * 3, 1.0)
    return round(score, 4)


# ─────────────────────────────────────────────────────────────────────────────
#  Column warnings
# ─────────────────────────────────────────────────────────────────────────────

def _check_warnings(sig: dict, df: pd.DataFrame) -> List[str]:
    """Generate data-quality warnings specific to the detected domain."""
    warnings: List[str] = []
    sector = sig.get("sector", "general")

    # Missing value warnings for key columns
    for kw in sig.get("required_columns", []):
        for col in df.columns:
            if kw in _normalise(col):
                miss_pct = df[col].isnull().mean() * 100
                if miss_pct > 5:
                    warnings.append(
                        f"Column '{col}' has {miss_pct:.1f}% missing values — "
                        f"may affect {kw} KPI accuracy."
                    )

    # Negative value warnings for amount columns
    for col in df.select_dtypes(include="number").columns:
        col_n = _normalise(col)
        if any(kw in col_n for kw in ["amount", "premium", "claim", "revenue", "salary"]):
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                warnings.append(
                    f"Column '{col}' contains {neg_count} negative values — verify data."
                )

    # Date column warnings
    for kw in sig.get("date_indicators", []):
        for col in df.columns:
            if kw in _normalise(col):
                if df[col].dtype == object:
                    warnings.append(
                        f"Column '{col}' appears to be a date but is stored as text — "
                        f"consider parsing."
                    )

    return warnings[:6]  # cap at 6 warnings


# ─────────────────────────────────────────────────────────────────────────────
#  Main fingerprint function
# ─────────────────────────────────────────────────────────────────────────────

def fingerprint_dataset(df: pd.DataFrame) -> Optional[DomainContext]:
    """
    Analyse a DataFrame and return the best-matching DomainContext,
    or None if no signature scores above its min_match_score.

    Scoring:
        total = 0.40 * signal1 + 0.35 * signal2 + 0.25 * signal3
    """
    if df is None or df.empty:
        return None

    columns = list(df.columns)
    best_key   = None
    best_score = 0.0
    all_scores: Dict[str, float] = {}

    for sig_key, sig in DATASET_SIGNATURES.items():
        s1 = _signal_column_match(sig, columns)
        s2 = _signal_value_distribution(sig, df)
        s3 = _signal_pattern_match(sig, columns)

        total = round(0.40 * s1 + 0.35 * s2 + 0.25 * s3, 4)
        all_scores[sig_key] = total

        if total > best_score:
            best_score = total
            best_key   = sig_key

    logger.debug(f"Fingerprint scores: {all_scores}")
    logger.info(f"Best match: {best_key} score={best_score:.3f}")

    if best_key is None:
        return None

    sig = DATASET_SIGNATURES[best_key]
    min_score = sig.get("min_match_score", 0.45)

    if best_score < min_score:
        logger.info(
            f"Best score {best_score:.3f} below threshold {min_score} — returning general"
        )
        return _general_context(df)

    warnings = _check_warnings(sig, df)

    return DomainContext(
        sector               = sig["sector"],
        sub_sector           = sig["sub_sector"],
        confidence           = best_score,
        primary_kpis         = sig["primary_kpis"],
        analysis_template    = sig_key,
        benchmarks           = sig["benchmarks"],
        regulatory_framework = sig["regulatory_framework"],
        india_specific       = sig["india_specific"],
        auto_insights        = sig["auto_insights"],
        column_warnings      = warnings,
    )


def _general_context(df: pd.DataFrame) -> DomainContext:
    """Fallback DomainContext for unrecognised datasets."""
    return DomainContext(
        sector               = "general",
        sub_sector           = "general",
        confidence           = 0.0,
        primary_kpis         = [],
        analysis_template    = "general",
        benchmarks           = {},
        regulatory_framework = "None",
        india_specific       = False,
        auto_insights        = [
            "What are the key trends in this dataset?",
            "Are there any outliers or anomalies?",
            "What correlations exist between numeric columns?",
            "What data quality issues need attention?",
        ],
        column_warnings      = [],
    )
