"""
Vishleshak v2 — Proactive Insight Engine
==========================================
Runs as a background thread immediately after dataset upload.
Does NOT block the UI — fires and surfaces results via Streamlit
session state flags which app.py polls to show st.toast() alerts.

What it does:
  1. Silent statistical profile of the new dataset
  2. Compares to Tier 2 memory of same/similar past datasets
  3. Detects: metric drift, new nulls, distribution shifts, new categories,
     schema changes, domain-specific red flags (Finance / Insurance)
  4. Writes flags to  data/memory/<user_id>/proactive_<session_id>.json
  5. app.py polls that file and surfaces st.toast() for each flag

Usage in app.py:
    from agentic_core.proactive_engine import ProactiveEngine

    # On dataset upload — fire and forget
    engine = ProactiveEngine(user_id=st.session_state.user_id,
                             session_id=st.session_state.session_id)
    engine.run_async(df, dataset_hash, dataset_name)

    # In your main render loop — poll for flags
    flags = engine.poll_flags()
    for flag in flags:
        st.toast(flag["message"], icon=flag["icon"])
"""

import os
import json
import logging
import threading
import hashlib
from datetime import datetime
from typing import Optional, List, Dict

import pandas as pd
import numpy as np

logger = logging.getLogger("vishleshak.proactive")

try:
    from groq import Groq
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
except ImportError:
    GROQ_API_KEY = ""

MODEL_FAST = "llama-3.1-8b-instant"
FLAGS_DIR = "data/memory"

# Thresholds
MEAN_DRIFT_PCT = 0.15
NULL_SPIKE_PCT = 0.05
CARDINALITY_CHANGE = 0.20
CORRELATION_DRIFT = 0.25


def _silent_profile(df: pd.DataFrame) -> dict:
    """Lightweight profile — just what we need for comparison. No LLM."""
    profile = {"cols": {}, "shape": {"rows": len(df), "cols": len(df.columns)}}

    for col in df.columns:
        s = df[col]
        info = {
            "null_pct": round(s.isnull().mean() * 100, 2),
            "unique_cnt": int(s.nunique()),
        }
        if pd.api.types.is_numeric_dtype(s) and s.notna().any():
            info["mean"] = round(float(s.mean()), 4)
            info["std"] = round(float(s.std()), 4)
            info["median"] = round(float(s.median()), 4)
            info["type"] = "numeric"
        else:
            info["type"] = "categorical"
            info["top_values"] = list(s.value_counts().head(10).index.astype(str))

        profile["cols"][col] = info

    num_cols = [c for c, v in profile["cols"].items() if v["type"] == "numeric"]
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        pairs = []
        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                pairs.append((corr.columns[i], corr.columns[j], round(float(corr.iloc[i, j]), 3)))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        profile["top_corr"] = pairs[:3]

    return profile


def _compare_profiles(current: dict, past: dict, domain: str = "general") -> list[dict]:
    """Rule-based comparison. Returns list of flag dicts."""
    flags = []
    cur_cols = current.get("cols", {})
    past_cols = past.get("past_col_stats", {})

    if not past_cols:
        return flags

    cur_names = set(cur_cols.keys())
    past_names = set(past_cols.keys())
    new_cols = cur_names - past_names
    dropped = past_names - cur_names

    if new_cols:
        flags.append({"type": "schema", "severity": "medium", "icon": "🟡",
                      "message": f"New columns detected: {', '.join(list(new_cols)[:4])}"})
    if dropped:
        flags.append({"type": "schema", "severity": "high", "icon": "🔴",
                      "message": f"Columns removed vs last analysis: {', '.join(list(dropped)[:4])}"})

    for col in cur_names & past_names:
        cur_info = cur_cols.get(col, {})
        past_info = past_cols.get(col, {})

        if cur_info.get("type") != "numeric" or past_info.get("type") != "numeric":
            continue

        cur_mean = cur_info.get("mean")
        past_mean = past_info.get("mean")
        if cur_mean is None or past_mean is None or past_mean == 0:
            continue

        drift = abs(cur_mean - past_mean) / abs(past_mean)
        if drift > MEAN_DRIFT_PCT:
            direction = "increased" if cur_mean > past_mean else "decreased"
            severity = "high" if drift > 0.30 else "medium"
            flags.append({
                "type": "drift", "severity": severity,
                "icon": "🔴" if severity == "high" else "🟡", "col": col,
                "message": f"'{col}' mean {direction} by {drift*100:.1f}% ({past_mean:.2f} → {cur_mean:.2f})"
            })

    for col in cur_names & past_names:
        cur_null = cur_cols.get(col, {}).get("null_pct", 0)
        past_null = past_cols.get(col, {}).get("null_pct", 0)
        delta = cur_null - past_null
        if delta > NULL_SPIKE_PCT * 100:
            flags.append({
                "type": "nulls", "severity": "high" if delta > 10 else "medium",
                "icon": "🔴" if delta > 10 else "🟡", "col": col,
                "message": f"Null spike in '{col}': {past_null:.1f}% → {cur_null:.1f}% (+{delta:.1f}pts)"
            })

    for col in cur_names & past_names:
        cur_info = cur_cols.get(col, {})
        past_info = past_cols.get(col, {})
        if cur_info.get("type") != "categorical":
            continue
        cur_card = cur_info.get("unique_cnt", 0)
        past_card = past_info.get("unique_cnt", 0)
        if past_card == 0:
            continue
        change = abs(cur_card - past_card) / past_card
        if change > CARDINALITY_CHANGE:
            direction = "more" if cur_card > past_card else "fewer"
            flags.append({
                "type": "cardinality", "severity": "low", "icon": "🟢", "col": col,
                "message": f"'{col}' has {direction} categories: {past_card} → {cur_card} ({change*100:.0f}% change)"
            })

    for col in cur_names & past_names:
        cur_info = cur_cols.get(col, {})
        past_info = past_cols.get(col, {})
        if cur_info.get("type") != "categorical":
            continue
        cur_top = set(cur_info.get("top_values", []))
        past_top = set(past_info.get("top_values", []))
        new_vals = cur_top - past_top
        if new_vals and len(new_vals) <= 5:
            flags.append({
                "type": "new_values", "severity": "low", "icon": "🟢", "col": col,
                "message": f"New values in '{col}': {', '.join(list(new_vals)[:3])}"
            })

    cur_corr = {(a, b): r for a, b, r in current.get("top_corr", [])}
    past_corr = past.get("past_correlations", {})
    for (a, b), r in cur_corr.items():
        past_r = past_corr.get(f"{a}|{b}") or past_corr.get(f"{b}|{a}")
        if past_r is not None:
            delta = abs(r - past_r)
            if delta > CORRELATION_DRIFT:
                flags.append({
                    "type": "correlation", "severity": "medium", "icon": "🟡",
                    "message": f"Correlation between '{a}' and '{b}' shifted: {past_r:.2f} → {r:.2f} (Δ{delta:.2f})"
                })

    return flags


def _domain_checks(df: pd.DataFrame, profile: dict, domain: str) -> list[dict]:
    """Apply domain-specific heuristic rules to current dataset."""
    flags = []
    col_info = profile.get("cols", {})

    if domain == "insurance":
        claim_cols = [c for c in df.columns if "claim" in c.lower()]
        premium_cols = [c for c in df.columns if "premium" in c.lower()]
        if claim_cols and premium_cols:
            try:
                total_claims = df[claim_cols[0]].sum()
                total_premium = df[premium_cols[0]].sum()
                if total_premium > 0:
                    loss_ratio = total_claims / total_premium
                    if loss_ratio > 0.70:
                        flags.append({"type": "domain", "severity": "high", "icon": "🔴",
                                      "message": f"Loss ratio is {loss_ratio:.1%} — above 70% threshold."})
                    elif loss_ratio > 0.55:
                        flags.append({"type": "domain", "severity": "medium", "icon": "🟡",
                                      "message": f"Loss ratio is {loss_ratio:.1%} — approaching warning threshold."})
            except Exception:
                pass

        lapse_cols = [c for c in df.columns if any(k in c.lower() for k in ("lapse", "churn", "cancel"))]
        for col in lapse_cols:
            if col_info.get(col, {}).get("type") == "numeric":
                mean = col_info[col].get("mean", 0) or 0
                if mean > 0.25:
                    flags.append({"type": "domain", "severity": "high", "icon": "🔴",
                                  "message": f"'{col}' rate is {mean:.1%} — high lapse/churn signal."})

        for col in claim_cols:
            info = col_info.get(col, {})
            if info.get("type") == "numeric":
                mean = info.get("mean", 0) or 0
                std = info.get("std", 0) or 0
                if mean > 0 and std / mean > 2.0:
                    flags.append({"type": "domain", "severity": "medium", "icon": "🟡",
                                  "message": f"'{col}' has very high variance (CV={std/mean:.1f}) — potential issues."})

    elif domain == "finance":
        for col in df.columns:
            col_lower = col.lower()
            info = col_info.get(col, {})
            if info.get("type") != "numeric":
                continue
            mean = info.get("mean", 0) or 0
            if any(k in col_lower for k in ("revenue", "income", "profit", "sales")) and mean < 0:
                flags.append({"type": "domain", "severity": "high", "icon": "🔴",
                              "message": f"Negative mean in '{col}' ({mean:,.2f}) — potential loss period."})

        expense_cols = [c for c in df.columns if "expense" in c.lower() or "cost" in c.lower()]
        revenue_cols = [c for c in df.columns if "revenue" in c.lower() or "income" in c.lower()]
        if expense_cols and revenue_cols:
            try:
                exp = df[expense_cols[0]].sum()
                rev = df[revenue_cols[0]].sum()
                if rev > 0 and exp / rev > 0.80:
                    flags.append({"type": "domain", "severity": "high", "icon": "🔴",
                                  "message": f"Expense ratio is {exp/rev:.1%} — very high."})
            except Exception:
                pass

    return flags


def _llm_flags(profile: dict, rule_flags: list[dict], domain: str, dataset_name: str) -> list[dict]:
    """Ask fast LLM if rule-based checks missed anything obvious."""
    if not GROQ_API_KEY or len(rule_flags) >= 6:
        return []

    existing_messages = [f["message"] for f in rule_flags]
    shape = profile.get("shape", {})

    prompt = f"""You are a {domain} data analyst doing a quick anomaly scan.
Dataset: {dataset_name} | {shape.get('rows',0)} rows × {shape.get('cols',0)} cols
Rule-based flags: {existing_messages}
Column summary: {json.dumps({c: info.get('mean') for c, info in list(profile.get('cols', {}).items())[:10]}, indent=0)}
Identify up to 3 additional anomalies. Return ONLY JSON array of strings. Max 20 words each."""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=MODEL_FAST, messages=[{"role": "user", "content": prompt}],
            temperature=0.1, max_tokens=250,
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        msgs = json.loads(raw)
        if not isinstance(msgs, list):
            return []
        return [{"type": "llm", "severity": "low", "icon": "🟢", "message": str(m)} for m in msgs[:3]]
    except Exception as e:
        logger.warning(f"LLM flag synthesis failed: {e}")
        return []


def _flags_path(user_id: str, session_id: str) -> str:
    return os.path.join(FLAGS_DIR, user_id, f"proactive_{session_id}.json")


def _write_flags(user_id: str, session_id: str, flags: list[dict]):
    os.makedirs(os.path.join(FLAGS_DIR, user_id), exist_ok=True)
    path = _flags_path(user_id, session_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"flags": flags, "written_at": datetime.now().isoformat()}, f, indent=2)


def _read_and_clear_flags(user_id: str, session_id: str) -> list[dict]:
    """Read flags file, delete it, return flags. One-shot poll."""
    path = _flags_path(user_id, session_id)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
        os.remove(path)
        return data.get("flags", [])
    except Exception as e:
        logger.warning(f"Flag read failed: {e}")
        return []


def _run_proactive_worker(df: pd.DataFrame, dataset_hash: str, dataset_name: str,
                          user_id: str, session_id: str, domain: str):
    """Full proactive scan pipeline. Runs in a daemon thread."""
    try:
        logger.info(f"Proactive scan started: user={user_id} dataset={dataset_name}")
        all_flags = []

        current_profile = _silent_profile(df)

        try:
            from core.enhanced_memory import MemoryManager
            mm = MemoryManager(user_id=user_id, domain=domain)
            t2 = mm.load_tier2(dataset_hash)
            past_data = t2.get("col_stats_snapshot", {}) if t2 else {}
        except Exception as e:
            logger.warning(f"Memory manager error: {e}")
            past_data = {}

        if past_data:
            comparison_flags = _compare_profiles(current_profile, past_data, domain)
            all_flags.extend(comparison_flags)

        domain_flags = _domain_checks(df, current_profile, domain)
        all_flags.extend(domain_flags)

        llm_flags = _llm_flags(current_profile, all_flags, domain, dataset_name)
        all_flags.extend(llm_flags)

        seen = set()
        deduped = []
        for flag in all_flags:
            msg = flag.get("message", "")
            if msg not in seen:
                seen.add(msg)
                deduped.append(flag)

        order = {"high": 0, "medium": 1, "low": 2}
        deduped.sort(key=lambda x: order.get(x.get("severity", "low"), 2))

        _write_flags(user_id, session_id, deduped[:8])
        logger.info(f"Proactive scan complete: {len(deduped)} flags written")

    except Exception as e:
        logger.error(f"Proactive scan failed: {e}", exc_info=True)
        _write_flags(user_id, session_id, [])


class ProactiveEngine:
    """Fire-and-forget background scanner. Non-blocking."""

    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self._thread: Optional[threading.Thread] = None

    def run_async(self, df: pd.DataFrame, dataset_hash: str,
                  dataset_name: str, domain: str = "general"):
        """Start the proactive scan in a background daemon thread."""
        if self._thread and self._thread.is_alive():
            logger.info("Proactive scan already running — skipping duplicate trigger")
            return

        self._thread = threading.Thread(
            target=_run_proactive_worker,
            args=(df, dataset_hash, dataset_name, self.user_id, self.session_id, domain),
            daemon=True,
            name=f"proactive-{self.session_id[:8]}",
        )
        self._thread.start()
        logger.info(f"Proactive scan thread started: {self._thread.name}")

    def poll_flags(self) -> list[dict]:
        """Check if the background scan has finished and return any flags."""
        if self._thread and self._thread.is_alive():
            return []
        return _read_and_clear_flags(self.user_id, self.session_id)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def run_sync(self, df: pd.DataFrame, dataset_hash: str,
                 dataset_name: str, domain: str = "general") -> list[dict]:
        """Synchronous version — blocks until complete."""
        _run_proactive_worker(df, dataset_hash, dataset_name, self.user_id, self.session_id, domain)
        return _read_and_clear_flags(self.user_id, self.session_id)


# Legacy function for backward compatibility
def run_proactive_scan(state: dict) -> List[str]:
    """Legacy function - returns list of flag strings."""
    df = state.get("dataset")
    if df is None:
        return []
    
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "")
    flags = []
    
    try:
        memory_dir = os.path.join("data", "memory", user_id)
        if not os.path.exists(memory_dir):
            return flags
        
        past_files = [f for f in os.listdir(memory_dir) if f.endswith(".json")]
        
        for past_file in past_files:
            if past_file == f"{session_id}.json":
                continue
            try:
                with open(os.path.join(memory_dir, past_file), "r") as f:
                    past_data = json.load(f)
                similar_flags = _compare_datasets_legacy(df, past_data.get("meta", {}))
                flags.extend(similar_flags)
            except Exception:
                pass
        
        new_flags = _detect_new_anomalies(df)
        flags.extend(new_flags)
        flags = list(set(flags))[:5]
        
    except Exception as e:
        logger.warning(f"Proactive scan error: {e}")
    
    return flags


def _compare_datasets_legacy(current_df: pd.DataFrame, past_meta: dict) -> List[str]:
    """Legacy comparison function."""
    flags = []
    if not past_meta:
        return flags
    
    current_shape = current_df.shape
    past_shape = past_meta.get("shape", [0, 0])
    
    if current_shape[0] != past_shape[0]:
        row_diff = current_shape[0] - past_shape[0]
        if abs(row_diff) / max(past_shape[0], 1) > 0.2:
            flags.append(f"Dataset row count changed by {row_diff:+d}")
    
    current_cols = set(current_df.columns)
    past_cols = set(past_meta.get("columns", []))
    
    new_cols = current_cols - past_cols
    if new_cols:
        flags.append(f"New columns detected: {', '.join(list(new_cols)[:3])}")
    
    dropped_cols = past_cols - current_cols
    if dropped_cols:
        flags.append(f"Columns removed: {', '.join(list(dropped_cols)[:3])}")
    
    return flags


def _detect_new_anomalies(df: pd.DataFrame) -> List[str]:
    """Legacy anomaly detection."""
    flags = []
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    for col in numeric_cols[:5]:
        try:
            data = df[col].dropna()
            if len(data) < 10:
                continue
            
            from scipy import stats as scipy_stats
            z_scores = np.abs(scipy_stats.zscore(data))
            outlier_count = (z_scores > 3).sum()
            outlier_pct = outlier_count / len(data) * 100
            
            if outlier_pct > 5:
                flags.append(f"High outliers in '{col}' ({outlier_pct:.1f}%)")
            
            null_pct = df[col].isnull().sum() / len(df) * 100
            if null_pct > 20:
                flags.append(f"High missing values in '{col}' ({null_pct:.1f}%)")
        
        except Exception:
            continue
    
    return flags


def save_proactive_memory(state: dict, flags: List[str]):
    """Save current dataset metadata for future comparisons."""
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "")
    
    try:
        memory_dir = os.path.join("data", "memory", user_id)
        os.makedirs(memory_dir, exist_ok=True)
        
        df = state.get("dataset")
        meta = {
            "shape": list(df.shape) if df is not None else [0, 0],
            "columns": list(df.columns) if df is not None else [],
            "dtypes": df.dtypes.astype(str).to_dict() if df is not None else {},
            "saved_at": datetime.now().isoformat(),
            "proactive_flags": flags
        }
        
        memory_file = os.path.join(memory_dir, f"{session_id}.json")
        with open(memory_file, "w") as f:
            json.dump({"meta": meta, "summary": state.get("insights_text", "")[:500]}, f)
        
        logger.info(f"✅ Saved proactive memory: {memory_file}")
    
    except Exception as e:
        logger.warning(f"Failed to save memory: {e}")