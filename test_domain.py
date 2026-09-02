import pytest
import pandas as pd
from backend.app_modules.agentic_core.domain_ontology import DomainContext, DATASET_SIGNATURES
from backend.app_modules.agentic_core.dataset_fingerprinter import fingerprint_dataset, _check_warnings
from backend.app_modules.agentic_core.kpi_library import compute_kpis_for_domain, KPI_REGISTRY
from backend.app_modules.agentic_core.domain_agent_mixin import enrich_state_with_domain, build_domain_system_prompt_addon

def test_domain_ontology_signatures():
    assert "insurance_claims" in DATASET_SIGNATURES
    assert DATASET_SIGNATURES["insurance_claims"]["sector"] == "insurance"

def test_fingerprint_dataset_insurance():
    df = pd.DataFrame({
        "claim_amount": [100, 200],
        "premium_amount": [150, 300],
        "policy_id": [1, 2]
    })
    domain_ctx = fingerprint_dataset(df)
    assert domain_ctx is not None
    assert domain_ctx.sector == "insurance"
    assert "loss_ratio" in domain_ctx.primary_kpis

def test_check_warnings():
    df = pd.DataFrame({"premium": [100]})
    # Fix parameter order: sig, df
    warnings = _check_warnings({"column_warnings": ["missing claim"]}, df)
    assert isinstance(warnings, list)

def test_compute_kpis_for_domain():
    df = pd.DataFrame({
        "claims_incurred": [68],
        "net_premium": [100],
        "policy_id": [1]
    })
    dc = fingerprint_dataset(df)
    kpis = compute_kpis_for_domain(df, dc)
    assert "loss_ratio" in kpis
    assert kpis["loss_ratio"] == 0.68 or kpis["loss_ratio"].get("value") == 0.68

def test_enrich_state_with_domain():
    df = pd.DataFrame({
        "claims_incurred": [68],
        "net_premium": [100],
        "policy_id": [1]
    })
    state = {"dataset": df}
    enriched = enrich_state_with_domain(state)
    assert "domain_context" in enriched
    assert "domain_kpis" in enriched
    # Accept dict or dataclass
    dc = enriched["domain_context"]
    assert dc["sector"] == "insurance" if isinstance(dc, dict) else dc.sector == "insurance"

def test_build_domain_system_prompt_addon():
    df = pd.DataFrame({
        "claims_incurred": [68],
        "net_premium": [100],
        "policy_id": [1]
    })
    state = {"dataset": df}
    enriched = enrich_state_with_domain(state)
    addon = build_domain_system_prompt_addon(enriched)
    assert "domain: insurance" in addon or "Domain context" in addon or "Sector: insurance" in addon
