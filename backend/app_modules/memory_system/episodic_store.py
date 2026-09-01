import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict
import os

DB_PATH = 'data/memory/episodic.db'

def init_db():
    os.makedirs('data/memory', exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                dataset_name TEXT,
                sector TEXT,
                instruction TEXT,
                headline TEXT,
                key_findings TEXT,
                kpi_snapshot TEXT,
                dataset_hash TEXT,
                row_count INTEGER,
                col_count INTEGER,
                created_at TEXT,
                expires_at TEXT
            )
        ''')

def _hash_cols(columns: List[str]) -> str:
    return hashlib.md5(','.join(sorted(columns)).encode()).hexdigest()

def save_analysis_memory(user_id: str, state: dict) -> str:
    init_db()
    import uuid
    mem_id = str(uuid.uuid4())
    
    ds = state.get('dataset')
    cols = list(ds.columns) if ds is not None and hasattr(ds, 'columns') else []
    d_hash = _hash_cols(cols)
    
    res = state.get('analysis_result', {})
    if isinstance(res, dict):
        headline = str(res.get('executive_summary', ''))[:250]
        insights = res.get('key_insights', [])
        findings = json.dumps(insights if isinstance(insights, list) else [])
    else:
        headline = str(res)[:250]
        findings = '[]'
    
    kpis = state.get('domain_kpis', {})
    
    dc = state.get('domain_context')
    sector = dc.get('sector', dc.sector if hasattr(dc, 'sector') else 'general') if dc else 'general'
    
    now = datetime.now()
    expires = now + timedelta(days=90)
    
    row_count = state.get('dataset_meta', {}).get('profile', {}).get('rows', 0)
    if isinstance(state.get('row_count'), int):
        row_count = state.get('row_count')
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            'INSERT INTO analyses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                mem_id, 
                user_id, 
                state.get('dataset_name', state.get('source_path', '')),
                sector,
                state.get('instruction', state.get('user_query', '')),
                headline, 
                findings, 
                json.dumps(kpis), 
                d_hash,
                row_count,
                len(cols), 
                now.isoformat(), 
                expires.isoformat()
            )
        )
    return mem_id

def recall_for_dataset(user_id: str, dataset_hash: str, limit: int = 3) -> list:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            'SELECT * FROM analyses WHERE user_id=? AND dataset_hash=? ORDER BY created_at DESC LIMIT ?',
            (user_id, dataset_hash, limit)
        )
        return [dict(r) for r in cur.fetchall()]

def recall_recent(user_id: str, sector: str = '', limit: int = 5) -> list:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if sector:
            cur = conn.execute(
                'SELECT * FROM analyses WHERE user_id=? AND sector=? ORDER BY created_at DESC LIMIT ?',
                (user_id, sector, limit)
            )
        else:
            cur = conn.execute(
                'SELECT * FROM analyses WHERE user_id=? ORDER BY created_at DESC LIMIT ?',
                (user_id, limit)
            )
        return [dict(r) for r in cur.fetchall()]

def build_episodic_context(user_id: str, state: dict) -> str:
    ds = state.get('dataset')
    if ds is None or not hasattr(ds, 'columns'): 
        return ''
    
    d_hash = _hash_cols(list(ds.columns))
    past = recall_for_dataset(user_id, d_hash, 2)
    if not past: return ''
    
    lines = ['[Past Analyses of similar datasets]']
    for p in past:
        lines.append(f"- {p['created_at'][:10]}: {p['instruction']}")
        lines.append(f"  Headline: {p['headline']}")
        k = json.loads(p.get('kpi_snapshot', '{}'))
        if k:
            kl = ', '.join(f"{kn}={kv}" for kn,kv in k.items())
            lines.append(f"  Past KPIs: {kl}")
    return chr(10).join(lines)
