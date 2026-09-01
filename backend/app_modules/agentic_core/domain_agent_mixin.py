"""Phase 2A Domain Agent Mixin

Adds:
- enrich_state_with_domain(state)
  * fingerprint dataset to DomainContext
  * compute KPI values for that domain
- build_domain_system_prompt_addon(state)
  * returns a prompt addon string for agents

Designed to be safe: if any step fails, it degrades gracefully.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import logging

import pandas as pd

from .dataset_fingerprinter import fingerprint_dataset
from .kpi_library import compute_kpis_for_domain

logger = logging.getLogger("vishleshak.domain_mixin")


def enrich_state_with_domain(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich agent state with domain_context and domain_kpis.

    Expected keys:
      - state["df"] or state["dataset"]: pd.DataFrame
      - state["user_query"] (optional)

    Writes:
      - state["domain_context"]: dict (serialized DomainContext)
      - state["domain_kpis"]: dict {kpi_name: {"value": float, "benchmark": float|None}}
    """

    df: Optional[pd.DataFrame] = state.get("df") or state.get("dataset")
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return state

    try:
        ctx = fingerprint_dataset(df)
        if ctx is None:
            return state

        # compute KPIs (best-effort)
        kpis = compute_kpis_for_domain(df=df, domain_context=ctx)

        state["domain_context"] = {
            "sector": ctx.sector,
            "sub_sector": ctx.sub_sector,
            "confidence": ctx.confidence,
            "primary_kpis": ctx.primary_kpis,
            "analysis_template": ctx.analysis_template,
            "benchmarks": ctx.benchmarks,
            "regulatory_framework": ctx.regulatory_framework,
            "india_specific": ctx.india_specific,
            "auto_insights": ctx.auto_insights,
            "column_warnings": ctx.column_warnings,
        }
        state["domain_kpis"] = kpis
        return state

    except Exception as e:
        logger.warning("enrich_state_with_domain failed: %s", e)
        # ensure keys exist (so downstream doesn't crash)
        state.setdefault("domain_context", None)
        state.setdefault("domain_kpis", {})
        return state


def build_domain_system_prompt_addon(state: Dict[str, Any]) -> str:
    """Create a system-prompt addon from detected domain.

    If domain_context isn't available, returns empty string.
    """

    ctx = state.get("domain_context")
    if not ctx:
        return ""

    sector = ctx.get("sector", "general")
    confidence = ctx.get("confidence", 0.0)
    regulatory = ctx.get("regulatory_framework", "None")
    warnings = ctx.get("column_warnings", []) or []

    kpis = state.get("domain_kpis", {}) or {}
    kpi_lines = []
    for k, v in list(kpis.items())[:8]:
        val = v.get("value")
        bench = v.get("benchmark")
        if bench is None:
            kpi_lines.append(f"- {k}: {val}")
        else:
            kpi_lines.append(f"- {k}: {val} (benchmark={bench})")

    warn_block = "" 
    if warnings:
        warn_block = "\nData quality warnings:\n" + "\n".join(f"- {w}" for w in warnings[:6])

    return (
        "You are operating with detected domain intelligence.\n"
        f"Detected domain: {sector} (confidence={confidence:.2f}).\n"
        f"Regulatory framework (if applicable): {regulatory}.\n"
        + ("\nAuto-computed domain KPIs:\n" + "\n".join(kpi_lines) if kpi_lines else "")
        + warn_block
    )

