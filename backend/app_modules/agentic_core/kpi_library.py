"""Phase 2A KPI Library

Implements domain KPIs and a small KPI registry.

This repo currently relies on domain intelligence primarily for insurance
(loss_ratio etc). The implementation is best-effort and safe:
- returns None if required columns are missing
- never raises during KPI computation
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional
import logging

import pandas as pd

logger = logging.getLogger("vishleshak.kpi_library")


def _find_col(df: pd.DataFrame, *hints: str) -> Optional[str]:
    """Find first column matching any hint (case-insensitive partial)."""
    cols = list(df.columns)
    for hint in hints:
        if hint is None:
            continue
        h = hint.strip().lower()
        for col in cols:
            if h and h in str(col).lower():
                return col
    return None


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def loss_ratio(df: pd.DataFrame) -> Optional[float]:
    """Claims incurred / net premium.

    Insurance convention:
      loss_ratio = sum(claims_incurred) / sum(net_premium)

    Column hints supported:
      claims_incurred, claims_incurred_amount, claims_paid, claim_amount,
      incurred, loss
      net_premium, earned_premium, premium, net_premium_amount
    """
    c = _find_col(df, "claims_incurred", "claims_paid", "claims_incurred", "claim_amount", "claim_amt", "incurred", "loss")
    p = _find_col(df, "net_premium", "earned_premium", "premium_amount", "premium")
    if not c or not p:
        return None

    c_s = _to_numeric(df[c]).dropna()
    p_s = _to_numeric(df[p]).dropna()
    denom = float(p_s.sum()) if len(p_s) else 0.0
    if denom == 0.0:
        return None

    return round(float(c_s.sum()) / denom, 6)


def claims_frequency(df: pd.DataFrame) -> Optional[float]:
    """Claims count per policy (best-effort).

    Hints:
      claim (count), claims_count
      policy (policy count)
    """
    claim_col = _find_col(df, "claims_count", "claim_count", "claims", "claim")
    policy_col = _find_col(df, "policy", "policies", "policy_id", "contract")
    if not claim_col or not policy_col:
        return None

    claims = _to_numeric(df[claim_col]).dropna()
    policies = _to_numeric(df[policy_col]).dropna()
    denom = float(policies.count()) if policies is not None else 0.0
    if denom == 0.0:
        return None

    # If claim_col is already a count per row, sum it. Otherwise count rows.
    # We treat: numeric claim_col values as claim amounts/counts.
    return round(float(claims.sum()) / denom, 6) if len(claims) else 0.0


def settlement_ratio(df: pd.DataFrame) -> Optional[float]:
    """Settled claims / total claims.

    Hints:
      settled column + claim column
      settlement_date presence is treated as settled if boolean-ish.
    """
    settled_col = _find_col(df, "settled", "claim_settled", "is_settled")
    claim_amt_col = _find_col(df, "claims_incurred", "claims_paid", "claim_amount", "claim_amt", "incurred", "loss")
    if settled_col and claim_amt_col:
        settled = _to_numeric(df[settled_col]).fillna(0)
        total = _to_numeric(df[claim_amt_col]).fillna(0)
        denom = float(total.sum())
        if denom == 0.0:
            return None
        return round(float(settled.sum()) / denom, 6)

    # Alternative: use boolean settled_col if present and claim_amt_col missing
    if settled_col:
        settled = _to_numeric(df[settled_col]).fillna(0)
        denom = float(len(settled))
        if denom == 0.0:
            return None
        return round(float((settled > 0).sum()) / denom, 6)

    return None


def average_claim_size(df: pd.DataFrame) -> Optional[float]:
    """Average claim amount.

    Hints:
      claim_amount / claim_amt / claims_incurred
    """
    c = _find_col(df, "claim_amount", "claim_amt", "claims_incurred", "claims_paid", "incurred", "loss")
    if not c:
        return None
    s = _to_numeric(df[c]).dropna()
    if s.empty:
        return None
    return round(float(s.mean()), 6)


def outstanding_claims_ratio(df: pd.DataFrame) -> Optional[float]:
    """Outstanding claims / total claims.

    Hints:
      outstanding
      claim_amount as total
    """
    out_col = _find_col(df, "outstanding", "outstanding_claims", "open_claims")
    total_col = _find_col(df, "claim_amount", "claim_amt", "claims_incurred", "claims_paid", "incurred", "loss")
    if not out_col or not total_col:
        return None
    out_s = _to_numeric(df[out_col]).fillna(0)
    tot_s = _to_numeric(df[total_col]).fillna(0)
    denom = float(tot_s.sum())
    if denom == 0.0:
        return None
    return round(float(out_s.sum()) / denom, 6)


KPI_REGISTRY: Dict[str, Callable[[pd.DataFrame], Optional[float]]] = {
    "loss_ratio": loss_ratio,
    "claims_frequency": claims_frequency,
    "settlement_ratio": settlement_ratio,
    "average_claim_size": average_claim_size,
    "outstanding_claims_ratio": outstanding_claims_ratio,
}


def compute_kpis_for_domain(df: pd.DataFrame, domain_context: Any) -> Dict[str, Dict[str, Any]]:
    """Compute KPIs listed in domain_context.primary_kpis.

    Returns:
      {kpi_name: {"value": float|None, "benchmark": float|None}}
    """
    primary = []
    try:
        primary = getattr(domain_context, "primary_kpis", []) or domain_context.get("primary_kpis", [])
    except Exception:
        primary = []

    benchmarks = {}
    try:
        benchmarks = getattr(domain_context, "benchmarks", {}) or domain_context.get("benchmarks", {})
    except Exception:
        benchmarks = {}

    results: Dict[str, Dict[str, Any]] = {}

    for kpi_name in primary:
        fn = KPI_REGISTRY.get(kpi_name)
        if not fn:
            continue
        try:
            val = fn(df)
        except Exception:
            val = None

        bench = benchmarks.get(kpi_name) if isinstance(benchmarks, dict) else None
        results[kpi_name] = {"value": val, "benchmark": bench}

    # Ensure registry keys exist even if primary_kpis empty
    # (so downstream isn't empty in insurance case).
    return results

