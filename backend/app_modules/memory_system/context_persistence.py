import os
import json
from pathlib import Path
from datetime import datetime

PROFILE_DIR = Path('data/memory/users')

def load_context(user_id: str) -> dict:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    p = PROFILE_DIR / f"{user_id}.json"
    if p.exists():
        return json.loads(p.read_text())
    return {
        "business_profile": {"sector": "general"},
        "custom_kpis": {},
        "column_mappings": {},
        "preferences": {"preferred_charts": [], "insight_verbosity": "normal"},
        "kpi_history": {}
    }

def save_context(user_id: str, ctx: dict):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    p = PROFILE_DIR / f"{user_id}.json"
    p.write_text(json.dumps(ctx, indent=2))

def update_kpi_history(user_id: str, kpis: dict):
    ctx = load_context(user_id)
    hist = ctx.setdefault('kpi_history', {})
    ds = datetime.now().strftime("%Y-%m")
    for k, v in kpis.items():
        if k not in hist:
            hist[k] = []
        hist[k].append({"date": ds, "value": v})
        hist[k] = hist[k][-24:]
    save_context(user_id, ctx)

def auto_update_from_analysis(user_id: str, state: dict):
    dc = state.get('domain_context')
    sector = dc.get('sector', dc.sector if hasattr(dc, 'sector') else 'general') if dc else 'general'
    ctx = load_context(user_id)
    if ctx['business_profile'].get('sector') == 'general' and sector != 'general':
        ctx['business_profile']['sector'] = sector
        save_context(user_id, ctx)
    kpis = state.get('domain_kpis', {})
    if kpis:
        update_kpi_history(user_id, kpis)

def build_context_prompt(user_id: str) -> str:
    ctx = load_context(user_id)
    bp = ctx.get('business_profile', {})
    prefs = ctx.get('preferences', {})
    kh = ctx.get('kpi_history', {})
    
    lines = ["[Business Profiling Context]"]
    lines.append(f"Sector: {bp.get('sector', 'general')}")
    if prefs.get('insight_verbosity'):
        lines.append(f"Verbosity Preference: {prefs['insight_verbosity']}")
        
    s = "\n".join(lines)
    if kh:
        s += "\n[Historical KPIs]\n"
        for k, vlist in kh.items():
            if vlist:
                s += f"{k}: latest={vlist[-1]['value']} (from {vlist[-1]['date']})\n"
    return s
