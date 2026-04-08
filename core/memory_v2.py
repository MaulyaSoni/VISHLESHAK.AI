"""
Vishleshak v2 — Enhanced Memory (3-Tier Summarization)
========================================================
Tier 1 (Hot)  — current session buffer, raw messages, max 20 turns, in-memory
Tier 2 (Warm) — per-dataset summaries, generated after every analysis,
                 stored at data/memory/<user_id>/<dataset_hash>.json
Tier 3 (Cold) — long-term cross-session summary, auto-consolidated weekly,
                 stored at storage/memory_db/<user_id>/longterm.json
"""

import os
import json
import math
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger("vishleshak.memory")

HOT_MAX_TURNS = 20
HOT_TRIM_TO = 10
CONSOLIDATE_DAYS = 7

DOMAIN_KEYWORDS = {
    "finance": ["revenue", "profit", "loss", "cashflow", "margin", "debt", "equity", "volatility", "risk", "forecast", "expense", "budget"],
    "insurance": ["premium", "claim", "lapse", "churn", "loss ratio", "combined ratio", "irdai", "fraud", "solvency", "reserve", "mortality", "renewal"],
    "ecommerce": ["order", "customer", "cart", "churn", "basket", "return", "sku", "product", "revenue", "quantity"],
}


def _tier2_path(user_id: str, dataset_hash: str) -> str:
    return os.path.join("data", "memory", user_id, f"{dataset_hash}.json")

def _tier3_path(user_id: str) -> str:
    return os.path.join("storage", "memory_db", user_id, "longterm.json")

def _index_path(user_id: str) -> str:
    return os.path.join("data", "memory", user_id, "_index.json")


def importance_score(text: str, date_str: str, domain: str = "general") -> float:
    """Calculate importance score based on recency and domain keywords."""
    if not text:
        return 0.0
    
    try:
        age_days = (datetime.now() - datetime.fromisoformat(date_str)).days
    except:
        age_days = 30
    
    recency = math.exp(-age_days / 14.0)
    
    text_lower = text.lower()
    kw_list = DOMAIN_KEYWORDS.get(domain, []) + DOMAIN_KEYWORDS.get("finance", [])
    hits = sum(1 for kw in kw_list if kw in text_lower)
    density = min(hits / max(len(kw_list), 1), 0.5)
    
    length_signal = min(len(text) / 200.0, 0.15)
    
    score = 0.5 * recency + 0.35 * density + 0.15 * length_signal
    return round(score, 4)


def _tokenize_columns(columns: List[str]) -> set:
    tokens = set()
    for col in columns:
        for part in col.lower().replace("-", "_").split("_"):
            if len(part) > 2:
                tokens.add(part)
    return tokens


def column_similarity(cols_a: List[str], cols_b: List[str]) -> float:
    """Jaccard similarity between column name token sets."""
    a = _tokenize_columns(cols_a)
    b = _tokenize_columns(cols_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _groq_summarize(prompt: str, max_tokens: int = 400) -> str:
    """Call Groq LLM for summarization."""
    try:
        from core.llm import get_chat_llm
        llm = get_chat_llm()
        if llm:
            from langchain_core.output_parsers import StrOutputParser
            chain = llm | StrOutputParser()
            return chain.invoke(prompt).strip()
    except Exception as e:
        logger.warning(f"Groq summarize failed: {e}")
    return "[Summary unavailable]"


def _summarize_analysis(state: Dict) -> str:
    """Tier 2 summarization - generates compact summary after analysis."""
    meta = state.get("dataset_meta", {})
    domain = state.get("domain", "general")
    name = state.get("dataset_name", "dataset")
    profile = meta.get("profile", {})

    prompt = f"""
Summarise this data analysis in exactly 5 bullet points for future reference.
Be specific and quantitative. Each bullet max 25 words.

Dataset: {name} | Domain: {domain}
Shape: {profile.get('rows', 0)} rows x {profile.get('columns', 0)} cols
Missing: {profile.get('missing_pct', 0)}%
Numeric: {profile.get('numeric_count', 0)} columns

Return plain text, one bullet per line starting with "- ".
"""
    return _groq_summarize(prompt, max_tokens=350)


def _consolidate_tier2_to_tier3(entries: List[Dict], domain: str) -> str:
    """Tier 3 consolidation - compress all Tier 2 summaries into one."""
    if not entries:
        return ""

    combined = "\n\n".join([
        f"[{e.get('date_analysed', '?')} | {e.get('dataset_name', '?')}]\n{e.get('summary', '')}"
        for e in entries
    ][:3000])

    prompt = f"""
Extract the most important patterns and recurring trends across past dataset analyses.
Write 8-10 bullet points. Be specific. No preamble.

Past analyses:
{combined}

Return plain text, one bullet per line starting with "- ".
"""
    return _groq_summarize(prompt, max_tokens=600)


class MemoryManager:
    """
    3-tier memory manager for Vishleshak v2.
    """

    def __init__(self, user_id: str = "default", domain: str = "general"):
        self.user_id = user_id
        self.domain = domain
        self._hot: List[Dict] = []

        os.makedirs(os.path.join("data", "memory", user_id), exist_ok=True)
        os.makedirs(os.path.join("storage", "memory_db", user_id), exist_ok=True)

    def add_turn(self, role: str, content: str):
        """Add a chat turn to the hot buffer."""
        self._hot.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._hot) > HOT_MAX_TURNS:
            self._hot = self._hot[-HOT_TRIM_TO:]

    def get_hot_context(self, n: int = 6) -> List[Dict]:
        """Return last n turns as role/content dicts."""
        return [{"role": t["role"], "content": t["content"]} for t in self._hot[-n:]]

    def clear_hot(self):
        self._hot = []

    def save_analysis(self, state: Dict) -> str:
        """Generate and persist a Tier 2 summary."""
        dataset_hash = state.get("dataset_hash", "")
        if not dataset_hash:
            logger.warning("No dataset_hash - skipping Tier 2 save")
            return ""

        summary = _summarize_analysis(state)
        if not summary:
            return ""

        meta = state.get("dataset_meta", {})
        profile = meta.get("profile", {})
        
        entry = {
            "dataset_hash": dataset_hash,
            "dataset_name": state.get("dataset_name", "dataset"),
            "domain": state.get("domain", self.domain),
            "date_analysed": datetime.now().isoformat(),
            "summary": summary,
            "shape": meta.get("shape", {}),
            "columns": profile.get("numeric_columns", []) + profile.get("categorical_columns", []),
            "importance": importance_score(summary, datetime.now().isoformat(), self.domain),
        }

        path = _tier2_path(self.user_id, dataset_hash)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)

        self._update_index(entry)
        logger.info(f"Tier 2 saved: {path}")

        self._maybe_consolidate()
        return summary

    def load_tier2(self, dataset_hash: str) -> Optional[Dict]:
        """Load Tier 2 summary for a dataset hash."""
        path = _tier2_path(self.user_id, dataset_hash)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Tier 2 load failed: {e}")
            return None

    def find_similar_datasets(self, columns: List[str], threshold: float = 0.65) -> List[Dict]:
        """Search for past datasets with similar column structure."""
        index = self._load_index()
        matches = []
        for entry in index:
            past_cols = entry.get("columns", [])
            sim = column_similarity(columns, past_cols)
            if sim >= threshold:
                matches.append({**entry, "similarity": round(sim, 3)})
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:3]

    def load_tier3(self) -> Optional[Dict]:
        """Load Tier 3 long-term summary."""
        path = _tier3_path(self.user_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Tier 3 load failed: {e}")
            return None

    def force_consolidate(self) -> str:
        """Force Tier 3 consolidation."""
        return self._run_consolidation()

    def _maybe_consolidate(self):
        """Run Tier 3 if stale."""
        tier3 = self.load_tier3()
        if tier3:
            try:
                last = datetime.fromisoformat(tier3.get("last_consolidated", "2000-01-01"))
                if (datetime.now() - last).days < CONSOLIDATE_DAYS:
                    return
            except:
                pass
        self._run_consolidation()

    def _run_consolidation(self) -> str:
        """Read all Tier 2 entries and consolidate to Tier 3."""
        index = self._load_index()
        if len(index) < 2:
            return ""

        index.sort(key=lambda x: x.get("importance", 0), reverse=True)
        top_entries = index[:15]

        full_entries = []
        for e in top_entries:
            full = self.load_tier2(e["dataset_hash"])
            if full:
                full_entries.append(full)

        summary = _consolidate_tier2_to_tier3(full_entries, self.domain)
        if not summary:
            return ""

        tier3 = {
            "last_consolidated": datetime.now().isoformat(),
            "entries_processed": len(full_entries),
            "domain": self.domain,
            "summary": summary,
        }
        path = _tier3_path(self.user_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tier3, f, indent=2)

        logger.info(f"Tier 3 consolidated: {len(full_entries)} entries")
        return summary

    def load_context(self, dataset_hash: str = "", columns: List[str] = None) -> str:
        """Assemble memory context for supervisor."""
        ctx_parts = []

        if dataset_hash:
            t2 = self.load_tier2(dataset_hash)
            if t2:
                ctx_parts.append(
                    f"[Previously analysed on {t2.get('date_analysed', 'unknown')[:10]}]\n"
                    f"{t2.get('summary', '')}"
                )

        if not ctx_parts and columns:
            similar = self.find_similar_datasets(columns)
            if similar:
                best = similar[0]
                t2 = self.load_tier2(best["dataset_hash"])
                if t2:
                    ctx_parts.append(
                        f"[Similar dataset '{best.get('dataset_name', 'unknown')}' "
                        f"(similarity={best['similarity']})]\n"
                        f"{t2.get('summary', '')}"
                    )

        t3 = self.load_tier3()
        if t3 and t3.get("summary"):
            ctx_parts.append(
                f"[Long-term patterns from {t3.get('entries_processed', '?')} analyses]\n"
                f"{t3.get('summary', '')}"
            )

        return "\n\n---\n\n".join(ctx_parts)

    def _load_index(self) -> List[Dict]:
        path = _index_path(self.user_id)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def _update_index(self, entry: Dict):
        index = self._load_index()
        existing = next((i for i, e in enumerate(index) if e.get("dataset_hash") == entry["dataset_hash"]), None)
        
        lightweight = {
            "dataset_hash": entry["dataset_hash"],
            "dataset_name": entry["dataset_name"],
            "domain": entry["domain"],
            "date_analysed": entry["date_analysed"],
            "columns": entry.get("columns", []),
            "importance": entry.get("importance", 0),
        }
        
        if existing is not None:
            index[existing] = lightweight
        else:
            index.append(lightweight)

        with open(_index_path(self.user_id), "w") as f:
            json.dump(index, f, indent=2)

    def get_memory_stats(self) -> Dict:
        """Return memory state summary."""
        index = self._load_index()
        tier3 = self.load_tier3()
        return {
            "hot_turns": len(self._hot),
            "tier2_datasets": len(index),
            "tier3_exists": tier3 is not None,
            "tier3_last_update": (tier3 or {}).get("last_consolidated", "Never")[:16],
            "tier3_entries": (tier3 or {}).get("entries_processed", 0),
        }

    def delete_dataset_memory(self, dataset_hash: str) -> bool:
        """Delete Tier 2 memory for a dataset."""
        path = _tier2_path(self.user_id, dataset_hash)
        if os.path.exists(path):
            os.remove(path)
            index = [e for e in self._load_index() if e.get("dataset_hash") != dataset_hash]
            with open(_index_path(self.user_id), "w") as f:
                json.dump(index, f, indent=2)
            return True
        return False

    def clear_all_memory(self):
        """Wipe all memory for user."""
        import shutil
        for base in [f"data/memory/{self.user_id}", f"storage/memory_db/{self.user_id}"]:
            if os.path.exists(base):
                shutil.rmtree(base)
                os.makedirs(base, exist_ok=True)
        self._hot = []
        logger.info(f"All memory cleared for user={self.user_id}")


_memory_managers = {}

def get_memory_manager(user_id: str = "default", domain: str = "general") -> MemoryManager:
    """Get or create MemoryManager instance."""
    key = f"{user_id}:{domain}"
    if key not in _memory_managers:
        _memory_managers[key] = MemoryManager(user_id, domain)
    return _memory_managers[key]