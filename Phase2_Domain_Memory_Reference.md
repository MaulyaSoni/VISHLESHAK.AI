# Vishleshak AI — Phase 2 Build Reference
**Domain Intelligence + Memory System + Orchestrator Integration**

---

## Overview

| | Phase 2A | Phase 2B |
|---|---|---|
| **Name** | Domain Intelligence | Memory System |
| **Goal** | Auto-detect financial dataset type, compute domain KPIs | Remember past analyses + business context across sessions |
| **New Files** | `domain_ontology.py`, `dataset_fingerprinter.py`, `kpi_library.py`, `domain_agent_mixin.py` | `episodic_store.py`, `context_persistence.py`, `memory_manager.py`, `memory_api.py` |
| **Tests** | `test_domain.py` — 6/6 | `test_memory.py` — 5/5 |
| **Duration** | 10–12 days | 8–10 days |
| **Differentiator** | Insurance CSV → IRDAI loss ratio auto-computed, no user prompt | 5th analysis: "Your loss ratio improved 3pp vs last quarter" |

---

## Phase 2A — Domain Intelligence

### Files to Create

```
domain_ontology.py        ← DomainContext dataclass + 12 DATASET_SIGNATURES
dataset_fingerprinter.py  ← fingerprint_dataset() — 3-signal scoring
kpi_library.py            ← 50 KPI functions + KPI_REGISTRY
domain_agent_mixin.py     ← enrich_state_with_domain() + build_domain_system_prompt_addon()
test_domain.py            ← 6 tests — run before integration
```

### DomainContext Dataclass

```python
@dataclass
class DomainContext:
    sector: str                  # "insurance"|"banking"|"ecommerce"|"finance"|"general"
    sub_sector: str              # "claims"|"health"|"motor"|"nbfc"...
    confidence: float            # 0.0–1.0
    primary_kpis: List[str]      # top 5 to auto-compute
    analysis_template: str
    benchmarks: Dict[str, float] # kpi_name → industry median
    regulatory_framework: str    # "IRDAI"|"RBI"|"SEBI"|"MCA"|"None"
    india_specific: bool
    auto_insights: List[str]     # 4 mandatory insight prompts
    column_warnings: List[str]   # data quality alerts for this domain
```

### DATASET_SIGNATURES Structure

Each entry in the dictionary:

```python
"insurance_claims": {
    "required_columns":       ["claim", "premium", "policy"],
    "optional_columns":       ["loss","incurred","settled","outstanding","zone","channel"],
    "numeric_indicators":     ["claim_amount","premium_amount","sum_insured"],
    "date_indicators":        ["claim_date","policy_date","settlement_date"],
    "categorical_indicators": ["policy_type","product_type","zone"],
    "min_match_score":        0.50,
    "sector":                 "insurance",
    "sub_sector":             "claims",
    "primary_kpis":           ["loss_ratio","claims_frequency","settlement_ratio",
                               "average_claim_size","outstanding_claims_ratio"],
    "regulatory_framework":   "IRDAI",
    "benchmarks": {
        "loss_ratio":       0.68,   # IRDAI industry median
        "combined_ratio":   0.98,
        "claims_frequency": 0.032,
        "settlement_ratio": 0.87,
    },
    "auto_insights": [
        "What is the loss ratio vs IRDAI median of 68%?",
        "Which product types have highest claims frequency?",
        "Geographic zones with abnormal claim patterns?",
        "What % of claims are settled vs outstanding?",
    ],
    "india_specific": True,
}
# Replicate for: banking_financials, ecommerce_orders, profit_loss,
# hr_payroll, gst_transactions, loan_portfolio, balance_sheet, nbfc_portfolio
```

### 3-Signal Fingerprinting Algorithm

| Signal | Weight | What It Checks |
|---|---|---|
| Column name matching | 40% | Partial match of signature keywords in uploaded column names |
| Value distribution | 35% | Numeric ranges sanity-check against domain benchmarks |
| Pattern matching | 25% | Columns ending in `_ratio`, `_amount`, `_date` matching domain conventions |

### KPI Library Pattern

```python
def _find_col(df, *hints):
    """Find first column matching any hint (case-insensitive partial)."""
    for hint in hints:
        for col in df.columns:
            if hint.lower() in col.lower(): return col
    return None

def loss_ratio(df) -> Optional[float]:
    """Claims Incurred / Net Premiums Earned. IRDAI median 68%."""
    c = _find_col(df, 'claims_incurred', 'claims_paid', 'claims_amount', 'claim_amt')
    p = _find_col(df, 'net_premium', 'earned_premium', 'premium_amount', 'premium')
    return round(df[c].sum() / df[p].sum(), 4) if c and p and df[p].sum() != 0 else None

KPI_REGISTRY = {
    "loss_ratio":      (loss_ratio,          "insurance", "Loss Ratio",     "%", 0.68),
    "combined_ratio":  (combined_ratio,      "insurance", "Combined Ratio", "%", 0.98),
    "nim":             (net_interest_margin, "banking",   "NIM",            "%", 0.031),
    "gnpa_ratio":      (gnpa_ratio,          "banking",   "GNPA Ratio",     "%", 0.038),
    "pat_margin":      (pat_margin,          "finance",   "PAT Margin",     "%", 0.082),
    # ... all 50 KPIs
}
```

### 4 Changes to data_agent_v3.py

**Change 1 — Import (after existing imports)**
```python
try:
    from domain_agent_mixin import enrich_state_with_domain, build_domain_system_prompt_addon
    DOMAIN_INTELLIGENCE = True
except ImportError:
    DOMAIN_INTELLIGENCE = False
    def enrich_state_with_domain(s): return s
    def build_domain_system_prompt_addon(s): return ''
```

**Change 2 — Enrich after load_csv in dispatch()**
```python
if name == 'load_csv' and DOMAIN_INTELLIGENCE and not state.get('domain_context'):
    state = enrich_state_with_domain(state)
    if state.get('domain_context'):
        ctx = state['domain_context']
        result += f'\nDomain: {ctx.sector} conf={ctx.confidence}'
```

**Change 3 — Inject into system prompt in run_agent()**
```python
domain_addon = build_domain_system_prompt_addon(state)
if domain_addon:
    messages[0]['content'] += '\n\n' + domain_addon
    print('  🧠 Domain context injected into system prompt')
```

**Change 4 — Add domain to compile_report output**
```python
'domain_context': {
    'sector':    state.get('domain_context').sector if state.get('domain_context') else 'general',
    'confidence':state.get('domain_context').confidence if state.get('domain_context') else 0,
    'kpis':      state.get('domain_kpis', {}),
    'regulatory':state.get('domain_context').regulatory_framework if state.get('domain_context') else 'None',
},
```

### 2 Changes to supervisor_graph.py

**Change 1 — Import**
```python
try:
    from domain_agent_mixin import enrich_state_with_domain
    DOMAIN_INTELLIGENCE = True
except ImportError:
    DOMAIN_INTELLIGENCE = False
    def enrich_state_with_domain(s): return s
```

**Change 2 — In data_agent() node after df_clean assigned**
```python
if DOMAIN_INTELLIGENCE and df_clean is not None:
    tmp = {'df': df_clean, 'instruction': state.get('user_query', ''),
           'errors': [], 'warnings': [], 'steps_taken': [],
           'domain_context': None, 'domain_kpis': {}}
    tmp = enrich_state_with_domain(tmp)
    if tmp.get('domain_context'):
        dc = tmp['domain_context']
        state['domain_context'] = {
            'sector': dc.sector, 'sub_sector': dc.sub_sector,
            'confidence': dc.confidence, 'kpis': tmp.get('domain_kpis', {}),
            'regulatory_framework': dc.regulatory_framework,
            'benchmarks': dc.benchmarks, 'auto_insights': dc.auto_insights
        }
        state['domain'] = dc.sector  # used by insight_agent
```

### Phase 2A Checklist

- [ ] `domain_ontology.py` — DomainContext class + 12 DATASET_SIGNATURES
- [ ] `dataset_fingerprinter.py` — fingerprint_dataset + _check_warnings
- [ ] `kpi_library.py` — 50 functions + KPI_REGISTRY + compute_kpis_for_domain
- [ ] `domain_agent_mixin.py` — enrich_state + build_domain_system_prompt_addon
- [ ] `test_domain.py` — created and passing **6/6**
- [ ] Change 1: import in `data_agent_v3.py`
- [ ] Change 2: enrich after load_csv in dispatch()
- [ ] Change 3: inject domain into system prompt
- [ ] Change 4: domain_context in compile_report
- [ ] 2 changes to `supervisor_graph.py`
- [ ] E2E test: insurance CSV → loss ratio in report ✓

---

## Phase 2B — Memory System

### 4-Tier Architecture

| Tier | Name | Stores | Retention | Technology |
|---|---|---|---|---|
| 1 | Working | Active session state | Session only | In-memory dict (already exists) |
| 2 | Episodic | Past analysis headlines + KPI snapshots | 90 days | SQLite → `episodic_store.py` |
| 3 | Semantic | Business profile, custom KPIs, column mappings | Permanent | JSON per user → `context_persistence.py` |
| 4 | Procedural | Learned preferences, chart types, verbosity | Permanent | JSON + pattern tracking |

### episodic_store.py — SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS analyses (
    id           TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL,
    dataset_name TEXT,
    sector       TEXT,
    instruction  TEXT,
    headline     TEXT,     -- executive_summary first 250 chars
    key_findings TEXT,     -- JSON array of strings
    kpi_snapshot TEXT,     -- JSON {kpi_name: {value, benchmark}}
    dataset_hash TEXT,     -- MD5 of sorted column names
    row_count    INTEGER,
    col_count    INTEGER,
    created_at   TEXT,
    expires_at   TEXT      -- created_at + 90 days
);
```

### Key Functions

```python
# episodic_store.py
def save_analysis_memory(user_id: str, state: dict) -> str:
    """Save analysis result after compile_report. Builds dataset_hash from columns."""

def recall_for_dataset(user_id, dataset_hash, limit=3) -> list:
    """Find past analyses of the same dataset schema."""

def recall_recent(user_id, sector='', limit=5) -> list:
    """Recent analyses, optionally filtered by sector."""

def build_episodic_context(user_id: str, state: dict) -> str:
    """Natural language string injected into system prompt."""

# context_persistence.py
def load_context(user_id: str) -> dict:
def save_context(user_id: str, ctx: dict):
def update_kpi_history(user_id, kpis):     # monthly time series, 24 months max
def auto_update_from_analysis(user_id, state):  # auto-sets sector + updates KPI history
def build_context_prompt(user_id) -> str:  # USER BUSINESS CONTEXT + KPI TRENDS
```

### JSON Profile Format (./memory/users/{user_id}.json)

```json
{
  "business_profile": {
    "sector": "insurance",
    "fiscal_year_start": "April",
    "regulatory_framework": "IRDAI",
    "currency": "INR"
  },
  "custom_kpis": {
    "adjusted_lr": "claims_net / (premium_earned * 0.97)"
  },
  "column_mappings": {"claims_amt": "claims_incurred"},
  "preferences": {
    "preferred_charts": ["bar", "scatter"],
    "insight_verbosity": "detailed"
  },
  "kpi_history": {
    "loss_ratio": [
      {"date": "2025-01", "value": 0.71},
      {"date": "2025-04", "value": 0.68}
    ]
  }
}
```

### memory_manager.py

```python
class MemoryManager:
    def load_context_for_agent(self, state: dict) -> str:
        # Combines Tier 2 episodic + Tier 3 semantic into one string
        # Injected into system prompt at start of run_agent()

    def save_after_analysis(self, state: dict):
        # Called after compile_report
        # Saves episodic entry + updates profile + KPI history

def get_memory_manager(user_id='default') -> MemoryManager:
    # Singleton per user_id
```

### 4 Changes to data_agent_v3.py

**Change 1 — Import**
```python
try:
    from memory_manager import get_memory_manager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    def get_memory_manager(uid='default'): return None
```

**Change 2 — user_id in fresh_state()**
```python
'user_id': 'default',  # overridden by FastAPI from auth token
```

**Change 3 — Load memory in run_agent()**
```python
if MEMORY_AVAILABLE:
    mm  = get_memory_manager(state.get('user_id', 'default'))
    mem = mm.load_context_for_agent(state)
    if mem:
        messages[0]['content'] += f'\n\n{mem}'
        print('  🧠 Memory context loaded')
```

**Change 4 — Save memory in tool_compile_report()**
```python
if MEMORY_AVAILABLE:
    try:
        get_memory_manager(state.get('user_id', 'default')).save_after_analysis(state)
        log(state, 'memory_saved')
    except Exception as e:
        state['warnings'].append(f'Memory save failed: {e}')
```

### Orchestrator Changes — supervisor_graph.py

**Replace memory_agent() node body:**
```python
def memory_agent(state: VishleshakState) -> VishleshakState:
    try:
        from memory_manager import get_memory_manager
        mm  = get_memory_manager(state.get('user_id', 'default'))
        ctx = mm.load_context_for_agent({
            'df': state.get('dataset'),
            'instruction': state.get('user_query', ''),
            'domain_context': None,
        })
        state['memory_context'] = ctx
    except Exception as e:
        logger.warning(f'Memory load failed: {e}')
        state['memory_context'] = ''
    return state
```

**Add to end of report_agent() node:**
```python
try:
    from memory_manager import get_memory_manager
    mm = get_memory_manager(state.get('user_id', 'default'))
    agent_state = {
        'final_report':   state.get('analysis_result', {}),
        'domain_context': None,
        'domain_kpis':    state.get('domain_context', {}).get('kpis', {}),
        'source_path':    state.get('dataset_name', ''),
        'row_count':      state.get('dataset_meta', {}).get('profile', {}).get('rows', 0),
        'instruction':    state.get('user_query', ''),
    }
    mm.save_after_analysis(agent_state)
except Exception as e:
    logger.warning(f'Memory save failed: {e}')
```

### FastAPI Routes (memory_api.py)

```python
GET  /memory/profile     → business_profile + preferences + custom_kpis
PUT  /memory/profile     → update business profile
GET  /memory/analyses    → past analyses (filter by sector)
GET  /memory/kpi_trends  → KPI time-series history

# Register in backend/main.py:
# from memory_api import router as memory_router
# app.include_router(memory_router)
```

### Phase 2B Checklist

- [ ] `episodic_store.py` — init_db, save, recall, build_episodic_context
- [ ] `context_persistence.py` — load, save, kpi_history, auto_update, build_prompt
- [ ] `memory_manager.py` — MemoryManager class + get_memory_manager()
- [ ] `memory_api.py` — 4 FastAPI routes
- [ ] `test_memory.py` — created and passing **5/5**
- [ ] Change 1: import in `data_agent_v3.py`
- [ ] Change 2: user_id in fresh_state()
- [ ] Change 3: load memory in run_agent()
- [ ] Change 4: save memory in compile_report()
- [ ] Replace `memory_agent()` in supervisor_graph.py
- [ ] Add memory save to `report_agent()` in supervisor_graph.py
- [ ] Register `memory_router` in backend/main.py
- [ ] E2E: same CSV twice → EPISODIC MEMORY in second run terminal ✓

---

## Phase 2 Debug Prompt (paste to Claude Code)

```
CONTEXT: Debugging Phase 2A (Domain Intelligence) + Phase 2B (Memory System).
3-week sprint confirmed working. Do NOT touch data_agent_v3.py core logic,
modal_sandbox.py, kaggle_tools.py, or supervisor_graph.py nodes other than
memory_agent() and report_agent(). Targeted additions only.

Source of truth: test_domain.py 6/6 + test_memory.py 5/5 = Phase 2 complete.
```

### P2A Debug

| Symptom | Bug | Fix |
|---|---|---|
| `fingerprint always returns 'general'` | P2A-01 | Print scores dict; lower min_match_score; add hint param |
| `KPI function returns None` | P2A-02 | Print `_find_col(df, 'claims_incurred', 'claim_amount')`; add actual column name as hint |
| `Domain context not in agent output` | P2A-03 | Check DOMAIN_INTELLIGENCE=True; verify enrich called after load_csv |
| `Supervisor domain is None` | P2A-04 | Print domain_context after tmp processing in data_agent() node |

### P2B Debug

| Symptom | Bug | Fix |
|---|---|---|
| `SQLite OperationalError` | P2B-01 | `DB_PATH.parent.mkdir(parents=True, exist_ok=True)` |
| `save_analysis_memory KeyError` | P2B-02 | Check state has: df, final_report.insights.executive_summary |
| `Memory empty on second run` | P2B-03 | Check user_id matches between runs; verify save succeeded |
| `KPI history not growing` | P2B-04 | Same-month guard skips duplicates; check kpis format `{name: {'value': float}}` |
| `memory_api 500 error` | P2B-05 | Check sys.path.insert at top + router registration in main.py |
| `supervisor memory_agent fails` | P2B-06 | Full replacement of function body, not append |

---

## Transition Gate — Phase 2 Complete

All 5 must pass before Phase 3:

```bash
# Gate 1
python test_domain.py
# Expected: 6/6 tests passed

# Gate 2
python test_memory.py
# Expected: 5/5 tests passed

# Gate 3 — upload insurance CSV and run analysis
# Expected terminal: 🎯 Domain: insurance/claims + loss_ratio in KPIs computed

# Gate 4 — run same CSV twice
# Expected terminal on second run: EPISODIC MEMORY — This dataset was analyzed before

# Gate 5
curl http://localhost:8000/memory/profile?user_id=default
# Expected: JSON with sector + kpi_history populated
```

---

## Orchestration Flow After Phase 2

```
supervisor_graph.invoke_supervisor():
  1. memory_agent()    → loads Tier 2 + Tier 3 into state['memory_context']
  2. intent_router()   → classifies domain (enhanced by memory context)
  3. data_agent()      → cleans data + enrich_state_with_domain() runs here
  4. insight_agent()   → gets domain + memory context via state
  5. viz_agent()       → generates charts
  6. report_agent()    → PDF + saves memory (Tier 2 + Tier 3 updated)

data_agent_v3.run_agent():
  1. fresh_state()     → includes user_id
  2. get_memory_manager() → loads context → injected into system prompt
  3. understand_intent → first tool
  4. load_csv          → triggers enrich_state_with_domain() in dispatch()
  5. ... pipeline ...
  6. compile_report    → saves memory at end
```

> **Critical ordering:** Memory loaded BEFORE pipeline. Domain detected DURING load_csv. Memory saved AFTER compile_report. Do not change this order.
