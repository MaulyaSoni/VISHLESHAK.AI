"""
Vishleshak AI — Data Analysis Agent v3 (Fixed)
================================================
Fixes:
  - Intent node: understands goal BEFORE running pipeline
  - Download: handles public datasets, GitHub raw, HuggingFace, redirects
  - Routing: app.py imports this as data_agent_v3 OR data_agent_3 (both work)
  - Orchestration: explicit step sequence based on intent
  - Progress: clean callback hook for Streamlit
"""

import json, os, re, sys, time, subprocess, traceback
from io import StringIO
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from groq import Groq

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
MODEL_SUPER    = "llama-3.1-8b-instant"
MODEL_INSIGHT  = "llama-3.3-70b-versatile"

MAX_LOOP_STEPS  = 25
MAX_CHUNK_ROWS  = 50_000
MAX_CHART_RETRY = 2
STEP_DELAY      = 1.2

# ─── progress hook (Streamlit patches this) ───
_progress_callback = None

def set_progress_callback(fn):
    """Streamlit calls this to receive step updates."""
    global _progress_callback
    _progress_callback = fn

def _emit(step: str, status: str = "done"):
    if _progress_callback:
        try:
            _progress_callback({"step": step, "status": status})
        except Exception:
            pass

def cancel_agent():
    global cancel_requested
    cancel_requested = True

# ─────────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────────
def fresh_state(instruction: str) -> dict:
    return {
        "instruction":    instruction,
        "intent":         {},        # parsed intent from intent_node
        "df":             None,
        "df_schema":      "",
        "source_path":    "",
        "row_count":      0,
        "col_count":      0,
        "preprocess_log": [],
        "eda":            {},
        "chart_specs":    [],
        "charts":         [],
        "insights":       {},
        "ml_results":     {},
        "notebook_path":  "",
        "errors":         [],
        "warnings":       [],
        "steps_taken":    [],
        "retry_counts":   {},
        "done":           False,
        "final_report":   {},
    }

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_client() -> Groq:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set. Run: export GROQ_API_KEY=your_key")
    return Groq(api_key=GROQ_API_KEY)

def groq_call(client, model, messages, tools=None, retries=5, max_tokens=1024):
    for attempt in range(retries):
        try:
            kw = dict(model=model, messages=messages, temperature=0.1, max_tokens=max_tokens)
            if tools:
                kw["tools"] = tools
                kw["tool_choice"] = "auto"
            return client.chat.completions.create(**kw)
        except Exception as e:
            if ("429" in str(e) or "rate_limit" in str(e).lower()) and attempt < retries - 1:
                wait = min(60, 4 ** attempt)
                print(f"    ⏳ 429 — waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Groq failed after all retries.")

def safe_json(raw: str):
    try:
        cleaned = re.sub(r"```json|```", "", raw).strip()
        if not cleaned.startswith("{"):
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                cleaned = match.group()
            else:
                return {"executive_summary": cleaned[:200], "key_findings": [], "anomalies_or_risks": [], "recommendations": [], "chart_interpretations": {}, "data_quality_note": "Insufficient data for full analysis."}
        return json.loads(cleaned)
    except Exception as e:
        return {"executive_summary": raw[:200], "key_findings": [], "anomalies_or_risks": [], "recommendations": [], "chart_interpretations": {}, "data_quality_note": f"Parse error: {str(e)}"}

def build_schema(df: pd.DataFrame, max_cols: int = 25) -> str:
    lines = ["COLUMNS (name | dtype | null% | sample)"]
    for col in df.columns[:max_cols]:
        np_ = round(df[col].isna().mean() * 100, 1)
        s   = df[col].dropna().head(3).tolist()
        lines.append(f"  {col} | {df[col].dtype} | {np_}% | {s}")
    lines.append(f"\nSHAPE: {df.shape[0]} × {df.shape[1]}")
    return "\n".join(lines)

def log(state: dict, step: str):
    state["steps_taken"].append(step)
    print(f"  → {step}")
    _emit(step, "done")

def safe_fn(title: str, n: int = 35) -> str:
    return re.sub(r"[^a-z0-9_]", "_", title.lower())[:n]

def save_chart(fig, title: str, idx: int, state: dict) -> dict:
    base = f"chart_{idx}_{safe_fn(title)}"
    html = f"{base}.html"
    png  = f"{base}.png"
    fig.update_layout(template="plotly_white",
                      margin=dict(l=50,r=50,t=60,b=50),
                      font=dict(family="Inter,Arial,sans-serif", size=12))
    fig.write_html(html)
    try:
        fig.write_image(png, width=900, height=520, scale=2)
    except Exception as e:
        png = ""
        state["warnings"].append(f"PNG export failed ('{title}'): {e}")
    return {"html_path": html, "png_path": png}

# ─────────────────────────────────────────────
#  TOOL 0: INTENT NODE  ← new, runs first
# ─────────────────────────────────────────────
def tool_understand_intent(state: dict, client: Groq) -> str:
    """
    Parse the user instruction into a structured intent before anything else.
    Determines: what file/url, what task type, what columns to focus on.
    """
    instr = state["instruction"]
    
    # Check if task type is already forced (from UI mode selection)
    existing_intent = state.get("intent", {})
    forced_task_type = existing_intent.get("task_type")
    
    prompt = f"""Parse this data analysis instruction into structured intent.
Return ONLY valid JSON, no markdown.

Instruction: "{instr}"

Return:
{{
  "task_type": "analysis_only | analysis_ml | analysis_ml_notebook",
  "data_source_type": "local_file | url | scan_folder | unknown",
  "data_source_value": "<filename, URL, or folder path if mentioned, else null>",
  "target_column": "<column to predict if ML task, else null>",
  "focus_columns": ["<col>"],
  "domain": "finance | insurance | ecommerce | general",
  "goals": ["<goal 1>", "<goal 2>"],
  "needs_download": true_or_false,
  "summary": "<one sentence: what the user wants to achieve>"
}}

Rules:
- If URL present → data_source_type=url, needs_download=true
- If filename like X.csv → data_source_type=local_file
- If "train", "predict", "model" → task_type=analysis_ml or analysis_ml_notebook
- If "notebook" → task_type=analysis_ml_notebook"""

    try:
        resp = groq_call(client, MODEL_INSIGHT,
                         [{"role": "user", "content": prompt}], max_tokens=500)
        intent = safe_json(resp.choices[0].message.content.strip())
        
        # If task type was forced from UI, use it instead of LLM's decision
        if forced_task_type:
            intent["task_type"] = forced_task_type
            print(f"  📌 Using forced task type: {forced_task_type}")
        
        state["intent"] = intent
        log(state, f"understand_intent → {intent.get('task_type')} | {intent.get('data_source_type')}")
        return (f"Intent parsed: task={intent['task_type']}, "
                f"source={intent['data_source_type']}={intent.get('data_source_value')}, "
                f"goal={intent.get('summary')}")
    except Exception as e:
        # Fallback intent - use forced task type if available
        fallback_task = forced_task_type or "analysis_only"
        state["intent"] = {
            "task_type": fallback_task,
            "data_source_type": "scan_folder",
            "data_source_value": ".",
            "needs_download": False,
            "summary": instr,
        }
        return f"Intent fallback (parse failed: {e}): will scan folder."

# ─────────────────────────────────────────────
#  TOOL 1: VALIDATE URL
# ─────────────────────────────────────────────
def tool_validate_url(state: dict, url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    path   = parsed.path.lower()

    if "kaggle.com/datasets" in url:
        log(state, "validate_url → Kaggle page")
        return ("KAGGLE_PAGE: Kaggle requires login. "
                "Use: kaggle datasets download -d <slug> --unzip "
                "OR provide a direct raw CSV URL. "
                "FALLBACK: scan_folder to check if already downloaded.")

    if "github.com" in domain and "/blob/" in url:
        raw = url.replace("github.com","raw.githubusercontent.com").replace("/blob/","/")
        log(state, f"validate_url → GitHub blob → raw URL")
        return f"GITHUB_RAW: Use this URL instead: {raw}"

    if "huggingface.co" in domain and "/resolve/" not in url:
        log(state, "validate_url → HuggingFace page")
        return ("HF_PAGE: Use resolve URL: "
                "https://huggingface.co/datasets/<owner>/<name>/resolve/main/<file>.csv")

    if path.endswith((".csv", ".tsv", ".zip")):
        log(state, "validate_url → direct file link")
        return f"DIRECT_FILE: Proceed with download_url."

    log(state, "validate_url → unknown, try download")
    return f"UNKNOWN_URL: Try download_url — may work if server returns CSV content."

# ─────────────────────────────────────────────
#  TOOL 2: DOWNLOAD URL  (improved)
# ─────────────────────────────────────────────
def tool_download_url(state: dict, url: str, save_as: str = "downloaded_data.csv") -> str:
    HEADERS = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"),
        "Accept": "text/csv,application/octet-stream,*/*",
    }
    try:
        # Google Drive
        if "drive.google.com" in url:
            m = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
            if m:
                url = f"https://drive.google.com/uc?id={m.group(1)}&export=download&confirm=t"

        # GitHub blob → raw
        if "github.com" in url and "/blob/" in url:
            url = url.replace("github.com","raw.githubusercontent.com").replace("/blob/","/")

        resp = requests.get(url, timeout=60, stream=True, headers=HEADERS,
                            allow_redirects=True)
        resp.raise_for_status()

        ct = resp.headers.get("content-type","").lower()
        if "text/html" in ct:
            return ("DOWNLOAD_FAILED: Server returned HTML page — not a direct file link. "
                    "Try: validate_url for the correct raw URL.")

        # Auto-detect extension from content-type or URL
        if ".zip" in url.lower() or "zip" in ct:
            save_as = save_as.replace(".csv", ".zip")
            is_zip  = True
        else:
            is_zip  = False

        total = 0
        with open(save_as, "wb") as f:
            for chunk in resp.iter_content(65536):
                f.write(chunk)
                total += len(chunk)
                if total > 300 * 1024 * 1024:
                    state["warnings"].append("File >300MB — stopped early.")
                    break

        # Unzip if needed
        if is_zip:
            import zipfile
            extract_dir = save_as.replace(".zip","_extracted")
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(save_as, "r") as z:
                z.extractall(extract_dir)
            csvs = list(Path(extract_dir).rglob("*.csv"))
            if csvs:
                save_as = str(csvs[0])
                log(state, f"download_url → unzipped → {save_as}")
                return f"Downloaded and unzipped. CSV at: {save_as}. Use load_csv('{save_as}')."

        log(state, f"download_url → {save_as} ({total//1024}KB)")
        return f"Downloaded '{save_as}' ({total//1024}KB). Use load_csv('{save_as}')."

    except Exception as e:
        state["errors"].append(f"Download failed: {e}")
        return f"DOWNLOAD_FAILED: {e}. Try scan_folder as fallback."

# ─────────────────────────────────────────────
#  TOOL 3: SCAN FOLDER
# ─────────────────────────────────────────────
def tool_scan_folder(state: dict, folder: str = ".") -> str:
    p = Path(folder)
    if not p.exists():
        return f"Folder '{folder}' not found."
    csvs = list(p.rglob("*.csv"))
    if not csvs:
        return f"No CSV files in '{folder}'."
    log(state, f"scan_folder → {len(csvs)} CSV(s)")
    return "Found CSVs:\n" + "\n".join(f"  {c}" for c in csvs[:20])

# ─────────────────────────────────────────────
#  TOOL 4: LOAD CSV
# ─────────────────────────────────────────────
def tool_load_csv(state: dict, path: str) -> str:
    try:
        chunks, total = [], 0
        for chunk in pd.read_csv(path, chunksize=10_000):
            chunks.append(chunk)
            total += len(chunk)
            if total >= MAX_CHUNK_ROWS:
                state["warnings"].append(f"Capped at {MAX_CHUNK_ROWS:,} rows.")
                break
        df = pd.concat(chunks, ignore_index=True)
        if df.empty:
            return "File is empty."
        state.update(df=df, df_schema=build_schema(df),
                     source_path=path, row_count=df.shape[0], col_count=df.shape[1])
        log(state, f"load_csv → {df.shape[0]:,}r × {df.shape[1]}c")
        return f"Loaded '{path}': {df.shape[0]:,} rows × {df.shape[1]} cols.\n{state['df_schema']}"
    except Exception as e:
        return f"LOAD_FAILED: {e}"

# ─────────────────────────────────────────────
#  TOOL 5: PREPROCESS
# ─────────────────────────────────────────────
def tool_preprocess(state: dict) -> str:
    if state["df"] is None:
        return "No data. Use load_csv first."
    try:
        df, lg = state["df"].copy(), []
        b = len(df); df.drop_duplicates(inplace=True)
        if (d := b - len(df)): lg.append(f"Removed {d} duplicates.")

        for col in df.columns[df.isna().mean() > 0.6]:
            df.drop(columns=[col], inplace=True); lg.append(f"Dropped '{col}' (>60% null).")

        for col in df.columns:
            if df[col].isna().sum() == 0: continue
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].median(), inplace=True); lg.append(f"'{col}' → median.")
            else:
                m = df[col].mode()
                if not m.empty: df[col].fillna(m[0], inplace=True); lg.append(f"'{col}' → mode.")

        for col in df.columns:
            if df[col].dtype == object and any(k in col.lower() for k in ["date","time","dt"]):
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce"); lg.append(f"'{col}' → datetime.")
                except: pass

        for col in df.select_dtypes(include=[np.number]).columns[:5]:
            Q1,Q3 = df[col].quantile([.25,.75]); IQR = Q3-Q1
            n = int(((df[col]<Q1-1.5*IQR)|(df[col]>Q3+1.5*IQR)).sum())
            if n: lg.append(f"'{col}': {n} outliers (kept).")

        state.update(df=df, df_schema=build_schema(df),
                     row_count=df.shape[0], preprocess_log=lg)
        log(state, f"preprocess → {len(lg)} steps")
        return "Done:\n" + "\n".join(f"  • {l}" for l in lg)
    except Exception as e:
        return f"PREPROCESS_FAILED: {e}"

# ─────────────────────────────────────────────
#  TOOL 6: EDA
# ─────────────────────────────────────────────
def tool_run_eda(state: dict) -> str:
    if state["df"] is None: return "No data."
    try:
        df, eda = state["df"], {}
        num = df.select_dtypes(include=[np.number])
        if not num.empty:
            eda["numeric_summary"] = num.describe().round(3).to_dict()
        cat = df.select_dtypes(include=["object","category"])
        ci  = {c: df[c].value_counts().head(5).to_dict() for c in cat.columns[:8]}
        if ci: eda["categorical_counts"] = ci
        if num.shape[1] > 1:
            corr  = num.corr().abs()
            mask  = np.triu(np.ones(corr.shape), k=1).astype(bool)
            pairs = corr.where(mask).stack().sort_values(ascending=False).head(8)
            eda["top_correlations"] = {str(k): round(v,3) for k,v in pairs.items()}
        missing = df.isna().sum(); missing = missing[missing>0]
        if not missing.empty: eda["remaining_nulls"] = missing.to_dict()
        eda["shape"] = {"rows": state["row_count"], "cols": state["col_count"]}
        state["eda"] = eda
        log(state, f"run_eda → {len(eda)} sections")
        lines = [f"EDA ({len(eda)} sections):"]
        if "numeric_summary" in eda:
            lines.append(f"  Numeric: {list(eda['numeric_summary'].keys())}")
        if "categorical_counts" in eda:
            lines.append(f"  Categorical: {list(eda['categorical_counts'].keys())}")
        if "top_correlations" in eda:
            lines.append(f"  Top correlations: {list(eda['top_correlations'].items())[:3]}")
        return "\n".join(lines)
    except Exception as e:
        return f"EDA_FAILED: {e}"

# ─────────────────────────────────────────────
#  TOOL 7: PLAN CHARTS
# ─────────────────────────────────────────────
def tool_plan_charts(state: dict, client: Groq) -> str:
    if not state["eda"]: return "Run run_eda first."
    try:
        prompt = f"""Return ONLY a JSON array of 2-3 chart specs. No markdown.
Use ONLY columns from schema.

Instruction: "{state['instruction']}"
Schema:\n{state['df_schema'][:700]}
EDA:\n{json.dumps(state['eda'],indent=2)[:1800]}

[{{"chart_type":"bar|line|scatter|histogram|heatmap|box",
   "x_col":"<col>","y_col":"<col or null>","color_col":"<col or null>",
   "title":"<title>","reasoning":"<why>"}}]"""

        resp  = groq_call(client, MODEL_INSIGHT, [{"role":"user","content":prompt}], max_tokens=600)
        raw   = resp.choices[0].message.content.strip()
        if not raw.startswith("["):
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            raw = m.group(0) if m else "[]"
        specs = json.loads(raw)
        valid = set(state["df"].columns) if state["df"] is not None else set()
        clean = []
        for s in specs:
            if s.get("x_col") not in valid: continue
            for k in ["y_col","color_col"]:
                if s.get(k) and s[k] not in valid: s[k] = None
            clean.append(s)
        state["chart_specs"] = clean
        log(state, f"plan_charts → {len(clean)}")
        return f"Planned {len(clean)}: " + ", ".join(s["title"] for s in clean)
    except Exception as e:
        return f"PLAN_CHARTS_FAILED: {e}"

# ─────────────────────────────────────────────
#  TOOL 8: GENERATE CHARTS
# ─────────────────────────────────────────────
BUILDERS = {
    "bar":       lambda df,s: px.bar(df,       x=s["x_col"],y=s.get("y_col"),  color=s.get("color_col"),title=s["title"]),
    "line":      lambda df,s: px.line(df,      x=s["x_col"],y=s.get("y_col"),  color=s.get("color_col"),title=s["title"]),
    "scatter":   lambda df,s: px.scatter(df,   x=s["x_col"],y=s.get("y_col"),  color=s.get("color_col"),title=s["title"]),
    "histogram": lambda df,s: px.histogram(df, x=s["x_col"],                   color=s.get("color_col"),title=s["title"]),
    "box":       lambda df,s: px.box(df,       x=s["x_col"],y=s.get("y_col"),  color=s.get("color_col"),title=s["title"]),
    "heatmap":   lambda df,s: go.Figure(go.Heatmap(
        z=df.select_dtypes(include=[np.number]).corr().round(2).values,
        x=df.select_dtypes(include=[np.number]).columns.tolist(),
        y=df.select_dtypes(include=[np.number]).columns.tolist(),
        colorscale="RdBu", zmid=0), layout=go.Layout(title=s["title"])),
}

def tool_generate_charts(state: dict) -> str:
    if not state["chart_specs"]: return "No specs. Run plan_charts first."
    if state["df"] is None: return "No data."
    df, results = state["df"], []
    for spec in state["chart_specs"]:
        title, cur = spec["title"], dict(spec)
        for attempt in range(MAX_CHART_RETRY+1):
            try:
                fig   = BUILDERS.get(cur["chart_type"], BUILDERS["bar"])(df, cur)
                paths = save_chart(fig, title, len(state["charts"])+1, state)
                state["charts"].append({**cur, "title":title,
                                        "html_path":paths["html_path"],
                                        "png_path": paths["png_path"], "spec":cur})
                results.append(f"✅ {cur['chart_type']}: {title} → {paths['html_path']}"
                               +(f" | {paths['png_path']}" if paths["png_path"] else ""))
                break
            except Exception as e:
                if attempt < MAX_CHART_RETRY:
                    nc = df.select_dtypes(include=[np.number]).columns.tolist()
                    cur = ({**cur,"x_col":nc[0],"y_col":nc[1],"chart_type":"scatter"}
                           if len(nc)>=2 and cur["chart_type"] in ["line","scatter"]
                           else {**cur,"chart_type":"histogram","x_col":nc[0],"y_col":None} if nc
                           else cur)
                    results.append(f"  ⚠ retry {attempt+1}")
                else:
                    state["errors"].append(f"Chart '{title}' failed: {e}")
                    results.append(f"❌ SKIPPED: {title}")
    log(state, f"generate_charts → {len(state['charts'])} saved")
    return "\n".join(results)

# ─────────────────────────────────────────────
#  TOOL 9: INSIGHTS
# ─────────────────────────────────────────────
def tool_generate_insights(state: dict, client: Groq) -> str:
    if not state["eda"]: return "Run run_eda first."
    try:
        chart_ctx = "\n".join(
            f"  [{c.get('type', 'unknown')}] '{c.get('title', 'Untitled')}' x={c.get('spec', {}).get('x_col')} y={c.get('spec', {}).get('y_col')}"
            for c in state["charts"]) or "  None."
        prompt = f"""Senior financial data analyst. Answer with specific numbers.
Return ONLY JSON.

Instruction: "{state['instruction']}"
Dataset: {state['row_count']:,}r × {state['col_count']}c
Schema:\n{state['df_schema'][:500]}
EDA:\n{json.dumps(state['eda'],indent=2)[:1600]}
Charts:\n{chart_ctx}
Preprocessing:\n{chr(10).join(state['preprocess_log'][:6])}

Return:
{{"executive_summary":"<3-4 sentences with numbers>",
  "key_findings":["<finding+stat>","<finding>","<finding>"],
  "anomalies_or_risks":["<anomaly>"],
  "recommendations":["<action>","<action>"],
  "chart_interpretations":{{"<title>":"<1-2 sentence interpretation>"}},
  "data_quality_note":"<limitations>"}}"""

        resp = groq_call(client, MODEL_INSIGHT, [{"role":"user","content":prompt}], max_tokens=1200)
        data = safe_json(resp.choices[0].message.content.strip())
        state["insights"] = data
        log(state, "generate_insights → done")
        return f"Insights done: {data.get('executive_summary','')[:100]}..."
    except Exception as e:
        state["errors"].append(f"Insights failed: {e}")
        return f"INSIGHTS_FAILED: {e}"

# ─────────────────────────────────────────────
#  PHASE 2 TOOLS (ML + Notebook)
# ─────────────────────────────────────────────
def tool_detect_target(state: dict, client: Groq, hint: str = "") -> str:
    if state["df"] is None: return "No data."
    intent = state.get("intent", {})
    # Use intent-parsed target if available
    if intent.get("target_column"):
        col = intent["target_column"]
        if col in state["df"].columns:
            valid_feats = [c for c in state["df"].columns if c != col]
            task = "regression" if pd.api.types.is_numeric_dtype(state["df"][col]) else "classification"
            state["ml_results"]["target_info"] = {
                "target_col": col, "task_type": task,
                "feature_cols": valid_feats, "reasoning": "From user instruction."
            }
            log(state, f"detect_target → '{col}' ({task}) from intent")
            return f"Target: '{col}' ({task}) — detected from instruction."

    try:
        prompt = f"""Identify the best ML target column.
Return ONLY JSON.

Instruction: "{hint or state['instruction']}"
Schema:\n{state['df_schema']}

{{"target_col":"<col>","task_type":"regression|classification",
  "feature_cols":["<col>"],"reasoning":"<why>"}}"""
        resp = groq_call(client, MODEL_INSIGHT, [{"role":"user","content":prompt}], max_tokens=400)
        data = safe_json(resp.choices[0].message.content.strip())
        valid = set(state["df"].columns)
        if data["target_col"] not in valid:
            return f"DETECT_FAILED: '{data['target_col']}' not in columns."
        data["feature_cols"] = [c for c in data.get("feature_cols",[]) if c in valid and c != data["target_col"]]
        state["ml_results"]["target_info"] = data
        log(state, f"detect_target → '{data['target_col']}' ({data['task_type']})")
        return f"Target: '{data['target_col']}' | {data['task_type']} | Features: {data['feature_cols']}"
    except Exception as e:
        return f"DETECT_FAILED: {e}"

def tool_train_model(state: dict) -> str:
    if state["df"] is None: return "No data."
    if "target_info" not in state["ml_results"]: return "Run detect_target first."
    try:
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing   import LabelEncoder
        from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
        import xgboost as xgb, shap

        info       = state["ml_results"]["target_info"]
        target_col = info["target_col"]
        feat_cols  = info["feature_cols"] or [c for c in state["df"].columns if c != target_col]
        task_type  = info["task_type"]
        df         = state["df"][feat_cols+[target_col]].copy().dropna()

        encoders = {}
        for col in df.select_dtypes(include=["object","category"]).columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le

        X, y = df[feat_cols], df[target_col]
        if task_type == "classification" and y.dtype == object:
            le = LabelEncoder(); y = le.fit_transform(y.astype(str))

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

        if task_type == "regression":
            model = xgb.XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.1,
                                     random_state=42, verbosity=0, n_jobs=-1)
        else:
            n_cl = len(np.unique(y))
            model = xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1,
                                      random_state=42, verbosity=0, n_jobs=-1,
                                      objective="binary:logistic" if n_cl==2 else "multi:softmax",
                                      num_class=n_cl if n_cl>2 else None)

        model.fit(X_tr, y_tr, eval_set=[(X_te,y_te)], verbose=False)
        y_pred = model.predict(X_te)

        metrics = ({"rmse": round(float(np.sqrt(mean_squared_error(y_te,y_pred))),4),
                    "r2_score": round(float(r2_score(y_te,y_pred)),4),
                    "mae": round(float(np.mean(np.abs(y_te-y_pred))),4)}
                   if task_type == "regression"
                   else {"accuracy": round(float(accuracy_score(y_te,y_pred)),4)})

        imp = dict(sorted(zip(feat_cols,[round(float(v),4) for v in model.feature_importances_]),
                          key=lambda x:-x[1])[:10])

        # SHAP
        shap_mean = imp
        try:
            bg = X_tr.sample(min(100,len(X_tr)),random_state=42)
            ex = shap.TreeExplainer(model, data=bg)
            sv = ex.shap_values(X_te[:200])
            if isinstance(sv, list): sv = sv[0]
            shap_mean = dict(sorted(zip(feat_cols,[round(float(v),4) for v in np.abs(sv).mean(axis=0)]),
                                    key=lambda x:-x[1])[:10])
            shap_df = pd.DataFrame({"feature":list(shap_mean.keys()),"importance":list(shap_mean.values())}).sort_values("importance")
            fig_s   = px.bar(shap_df, x="importance", y="feature", orientation="h", title="SHAP Feature Importance")
            sp      = save_chart(fig_s, "SHAP Feature Importance", len(state["charts"])+1, state)
            state["charts"].append({"title":"SHAP Feature Importance","type":"bar_h",
                                    "html_path":sp["html_path"],"png_path":sp["png_path"],
                                    "spec":{"x_col":"importance","y_col":"feature"}})
        except Exception as e:
            state["warnings"].append(f"SHAP skipped: {e}")

        state["ml_results"].update(task_type=task_type, target_col=target_col,
            feature_cols=feat_cols, metrics=metrics, feature_importance=imp,
            shap_importance=shap_mean, n_train=len(X_tr), n_test=len(X_te),
            model_obj=model, encoders={k:list(v.classes_) for k,v in encoders.items()})

        log(state, f"train_model → {task_type} metrics={metrics}")
        return f"Trained ({task_type}): {metrics} | top: {list(imp.keys())[:5]}"
    except Exception as e:
        state["errors"].append(f"Training failed: {e}")
        traceback.print_exc()
        return f"TRAIN_FAILED: {e}"

def tool_generate_notebook(state: dict) -> str:
    try:
        import nbformat
        from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

        ml, has_ml = state["ml_results"], bool(state["ml_results"].get("metrics"))
        cells = []
        cells.append(new_markdown_cell(
            f"# Vishleshak AI — Analysis Report\n\n"
            f"**Source:** `{state['source_path']}`  \n"
            f"**Instruction:** {state['instruction']}  \n"
            f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"))

        cells.append(new_code_cell(
            "import pandas as pd, numpy as np, plotly.express as px\n"
            "import warnings; warnings.filterwarnings('ignore')\n"
            +("import xgboost as xgb, shap\n"
              "from sklearn.model_selection import train_test_split\n"
              "from sklearn.preprocessing import LabelEncoder\n"
              "from sklearn.metrics import mean_squared_error,r2_score,accuracy_score\n" if has_ml else "")))

        cells.append(new_markdown_cell("## 1. Load Data"))
        cells.append(new_code_cell(f"df = pd.read_csv(r'{state['source_path']}')\nprint(df.shape)\ndf.head()"))

        cells.append(new_markdown_cell("## 2. Preprocessing\n\n"+"\n".join(f"- {l}" for l in state["preprocess_log"])))
        cells.append(new_code_cell(
            "df.drop_duplicates(inplace=True)\n"
            "for col in df.columns:\n"
            "    if df[col].isna().sum()==0: continue\n"
            "    if pd.api.types.is_numeric_dtype(df[col]): df[col].fillna(df[col].median(),inplace=True)\n"
            "    else: df[col].fillna(df[col].mode()[0],inplace=True)\n"
            "df.describe()"))

        cells.append(new_markdown_cell("## 3. EDA"))
        cells.append(new_code_cell(
            "print(df.describe().round(2))\nprint(df.isna().sum())\n"
            "num=df.select_dtypes(include=[float,int])\n"
            "if num.shape[1]>1:\n"
            "    corr=num.corr().abs(); mask=np.triu(np.ones(corr.shape),k=1).astype(bool)\n"
            "    print(corr.where(mask).stack().sort_values(ascending=False).head(5))"))

        cells.append(new_markdown_cell("## 4. Charts"))
        for c in state["charts"]:
            sp, ct = c["spec"], c["type"]
            code = (f"px.bar(df,x='{sp['x_col']}',y={repr(sp.get('y_col'))},title='{c['title']}').show()" if ct=="bar"
                    else f"px.histogram(df,x='{sp['x_col']}',title='{c['title']}').show()" if ct=="histogram"
                    else f"px.scatter(df,x='{sp['x_col']}',y={repr(sp.get('y_col'))},title='{c['title']}').show()")
            cells.append(new_code_cell(code))

        if has_ml:
            target, feats, task = ml["target_col"], ml["feature_cols"], ml["task_type"]
            cells.append(new_markdown_cell(
                f"## 5. ML — XGBoost {task.title()}\n**Target:** `{target}` | **Metrics:** {ml['metrics']}"))
            enc_code = ""
            for col in (ml.get("encoders") or {}):
                enc_code += f"df['{col}']=LabelEncoder().fit_transform(df['{col}'].astype(str))\n"
            model_cls = ("xgb.XGBRegressor(n_estimators=200,max_depth=4,learning_rate=0.1,random_state=42,verbosity=0)"
                         if task=="regression"
                         else "xgb.XGBClassifier(n_estimators=200,max_depth=4,learning_rate=0.1,random_state=42,verbosity=0)")
            metric_code = ("print(f'RMSE: {np.sqrt(mean_squared_error(y_te,y_pred)):.4f}')\nprint(f'R²: {r2_score(y_te,y_pred):.4f}')"
                           if task=="regression"
                           else "print(f'Accuracy: {accuracy_score(y_te,y_pred):.4f}')")
            cells.append(new_code_cell(
                f"{enc_code}\nX=df[{feats}].dropna()\ny=df.loc[X.index,'{target}']\n"
                f"X_tr,X_te,y_tr,y_te=train_test_split(X,y,test_size=0.2,random_state=42)\n"
                f"model={model_cls}\nmodel.fit(X_tr,y_tr)\ny_pred=model.predict(X_te)\n{metric_code}"))
            cells.append(new_markdown_cell("### SHAP"))
            cells.append(new_code_cell(
                "ex=shap.TreeExplainer(model)\nsv=ex.shap_values(X_te[:100])\n"
                "if isinstance(sv,list): sv=sv[0]\n"
                "sm=dict(zip(X_te.columns,np.abs(sv).mean(axis=0)))\n"
                "sdf=pd.DataFrame({'f':list(sm.keys()),'i':list(sm.values())}).sort_values('i')\n"
                "px.bar(sdf,x='i',y='f',orientation='h',title='SHAP').show()"))

        ins = state["insights"]
        if ins:
            md = f"## {'6' if has_ml else '5'}. Insights\n\n**Summary:** {ins.get('executive_summary','')}\n\n"
            md += "**Findings:**\n"+"\n".join(f"- {f}" for f in ins.get("key_findings",[]))
            md += "\n\n**Recommendations:**\n"+"\n".join(f"- {r}" for r in ins.get("recommendations",[]))
            cells.append(new_markdown_cell(md))

        nb      = new_notebook(cells=cells)
        nb_path = f"vishleshak_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.ipynb"
        with open(nb_path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        result = subprocess.run(
            ["jupyter","nbconvert","--to","notebook","--execute","--inplace",
             "--ExecutePreprocessor.timeout=120", nb_path],
            capture_output=True, text=True, timeout=180)

        status = "Executed ✅" if result.returncode==0 else f"Partial: {result.stderr[:100]}"
        state["notebook_path"] = nb_path
        log(state, f"generate_notebook → {nb_path}")
        return f"Notebook: {nb_path} | {status}"
    except ImportError as e:
        return f"NOTEBOOK_FAILED: pip install nbformat nbconvert — {e}"
    except Exception as e:
        return f"NOTEBOOK_FAILED: {e}"

def tool_compile_report(state: dict) -> str:
    try:
        eda = state.get("eda", {})
    except Exception:
        eda = {}
    try:
        insights = state.get("insights", {})
    except Exception:
        insights = {}
    try:
        ml_results = {k: v for k, v in state.get("ml_results", {}).items() if k != "model_obj"}
    except Exception:
        ml_results = {}
    try:
        warnings = state.get("warnings", [])
    except Exception:
        warnings = []
    try:
        errors = state.get("errors", [])
    except Exception:
        errors = []

    try:
        metadata_instruction = state.get("instruction", "")
    except Exception:
        metadata_instruction = ""
    try:
        metadata_source = state.get("source_path", "")
    except Exception:
        metadata_source = ""
    try:
        metadata_rows = state.get("row_count", 0)
    except Exception:
        metadata_rows = 0
    try:
        metadata_cols = state.get("col_count", 0)
    except Exception:
        metadata_cols = 0
    try:
        metadata_steps = state.get("steps_taken", [])
    except Exception:
        metadata_steps = []

    state["final_report"] = {
        "metadata": {"instruction": metadata_instruction, "source": metadata_source,
                     "rows": metadata_rows, "cols": metadata_cols,
                     "timestamp": pd.Timestamp.now().isoformat(),
                     "steps_taken": metadata_steps, "intent": state.get("intent", {})},
        "preprocessing": state.get("preprocess_log", {}),
        "eda": eda,
        "charts": [{"title": c.get("title", "Untitled"), "type": c.get("type", "unknown"),
                    "html_path": c.get("html_path", ""), "png_path": c.get("png_path", "")}
                   for c in state.get("charts", [])],
        "insights": insights,
        "ml_results": ml_results,
        "notebook_path": state.get("notebook_path", ""),
        "warnings": warnings,
        "errors": errors,
    }
    state["done"] = True
    with open("analysis_report.json","w") as f:
        json.dump(state["final_report"], f, indent=2, default=str)
    log(state, "compile_report → done")
    return "Report saved → analysis_report.json"

# ─────────────────────────────────────────────
#  TOOL REGISTRY
# ─────────────────────────────────────────────
TOOL_SCHEMAS = [
    {"type":"function","function":{"name":"understand_intent","description":"ALWAYS call this FIRST to parse the user instruction into a structured plan. Identifies data source, task type, and goals.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"validate_url","description":"Check if URL is direct CSV or webpage. Call before download_url.","parameters":{"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}}},
    {"type":"function","function":{"name":"scan_folder","description":"Find CSV files in local folder.","parameters":{"type":"object","properties":{"folder":{"type":"string"}},"required":[]}}},
    {"type":"function","function":{"name":"download_url","description":"Download CSV from direct URL. Handles zip, GitHub raw, Google Drive.","parameters":{"type":"object","properties":{"url":{"type":"string"},"save_as":{"type":"string"}},"required":["url"]}}},
    {"type":"function","function":{"name":"load_csv","description":"Load a local CSV file.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"preprocess","description":"Clean loaded data.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"run_eda","description":"Run exploratory data analysis.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"plan_charts","description":"Plan 2-3 best charts.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"generate_charts","description":"Generate and save all charts.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"generate_insights","description":"Generate analytical insights.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"detect_target","description":"Identify ML target column.","parameters":{"type":"object","properties":{"hint":{"type":"string"}},"required":[]}}},
    {"type":"function","function":{"name":"train_model","description":"Train XGBoost + SHAP.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"generate_notebook","description":"Build executed .ipynb notebook.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"compile_report","description":"Compile final report. Call LAST.","parameters":{"type":"object","properties":{},"required":[]}}},
]

# ─────────────────────────────────────────────
#  DISPATCHER
# ─────────────────────────────────────────────
def dispatch(name: str, args: dict, state: dict, client: Groq) -> str:
    print(f"\n  🔧 [{name}]")
    _emit(name, "running")
    state["retry_counts"][name] = state["retry_counts"].get(name,0)+1
    try:
        if name == "understand_intent":  return tool_understand_intent(state, client)
        if name == "validate_url":       return tool_validate_url(state, args.get("url",""))
        if name == "scan_folder":        return tool_scan_folder(state, args.get("folder","."))
        if name == "download_url":       return tool_download_url(state, args["url"], args.get("save_as","downloaded_data.csv"))
        if name == "load_csv":           return tool_load_csv(state, args["path"])
        if name == "preprocess":         return tool_preprocess(state)
        if name == "run_eda":            return tool_run_eda(state)
        if name == "plan_charts":        return tool_plan_charts(state, client)
        if name == "generate_charts":    return tool_generate_charts(state)
        if name == "generate_insights":  return tool_generate_insights(state, client)
        if name == "detect_target":      return tool_detect_target(state, client, args.get("hint",""))
        if name == "train_model":        return tool_train_model(state)
        if name == "generate_notebook":  return tool_generate_notebook(state)
        if name == "compile_report":     return tool_compile_report(state)
        return f"Unknown tool: {name}"
    except Exception as e:
        err = f"Tool '{name}' crashed: {e}"
        state["errors"].append(err)
        return err

# ─────────────────────────────────────────────
#  SYSTEM PROMPT
# ─────────────────────────────────────────────
SYSTEM = """You are Vishleshak, an autonomous data analysis agent.

MANDATORY FIRST STEP: Always call understand_intent FIRST, before any other tool.
It parses the user instruction into a structured plan you must follow.

ORCHESTRATION RULES (follow the intent output):
1. understand_intent → check data_source_type and task_type
2. data_source_type=url → validate_url → download_url (if DIRECT_FILE) → load_csv
3. data_source_type=local_file → load_csv directly
4. data_source_type=scan_folder → scan_folder → load_csv (pick most relevant file)
5. Always: load_csv → preprocess → run_eda → plan_charts → generate_charts → generate_insights
6. task_type=analysis_ml → add: detect_target → train_model
7. task_type=analysis_ml_notebook → add: detect_target → train_model → generate_notebook
8. Always end with: compile_report

FAILURE HANDLING:
- download fails → scan_folder as fallback
- load fails → scan_folder to find available files
- tool returns FAILED > 2x → skip and continue to next step
- Never stop early — always reach compile_report
"""

# ─────────────────────────────────────────────
#  REACT LOOP
# ─────────────────────────────────────────────
cancel_requested = False

def run_agent(instruction: str, force_task_type: str = None) -> dict:
    """
    Run the data analysis agent.
    
    Args:
        instruction: User's analysis instruction
        force_task_type: Optional - force a specific task type ('analysis_only', 'analysis_ml', 'analysis_ml_notebook')
    
    Returns:
        Complete analysis report dictionary
    """
    global cancel_requested
    cancel_requested = False
    
    print(f"\n{'═'*58}\n  Vishleshak Agent v3\n{'═'*58}\n  {instruction}\n{'═'*58}\n")

    client   = get_client()
    state    = fresh_state(instruction)
    
    # If task type is forced, set it in state before starting
    if force_task_type:
        state["intent"] = {"task_type": force_task_type}
        print(f"  📌 Forced task type: {force_task_type}")
    
    messages = [{"role":"system","content":SYSTEM},
                {"role":"user","content":instruction}]

    for step in range(MAX_LOOP_STEPS):
        if cancel_requested:
            print("\n  ⛔ Agent stopped by user.")
            state["errors"].append("Analysis stopped by user before completion.")
            break

        print(f"\n⟳  Step {step+1}/{MAX_LOOP_STEPS}")
        time.sleep(STEP_DELAY)

        resp = groq_call(client, MODEL_SUPER, messages, tools=TOOL_SCHEMAS, max_tokens=512)
        msg  = resp.choices[0].message

        if not msg.tool_calls:
            text = msg.content or ""
            print(f"  💬 {text[:200]}")
            messages.append({"role":"assistant","content":text})
            if state["done"]: break
            needed = _remaining(state)
            messages.append({"role":"user","content":
                f"Continue. Next required: {needed}. End with compile_report."})
            continue

        tc   = msg.tool_calls[0]
        name = tc.function.name
        args = json.loads(tc.function.arguments or "{}")

        messages.append({"role":"assistant","content":None,
            "tool_calls":[{"id":tc.id,"type":"function",
                           "function":{"name":name,"arguments":json.dumps(args)}}]})

        result = dispatch(name, args, state, client)
        print(f"     ↳ {str(result)[:220]}")

        # Self-correction
        if any(x in result for x in ["FAILED","not found","does not exist","Error"]):
            hint = _hint(name, state)
            result = result + f"\n\nCORRECTION: {hint}"

        messages.append({"role":"tool","tool_call_id":tc.id,"content":str(result)})
        if state["done"]: break

    # Summary
    ins = state["insights"]
    print(f"\n{'═'*58}\n  DONE — {len(state['steps_taken'])} steps, {len(state['charts'])} charts\n{'═'*58}")
    if ins.get("executive_summary"): print(f"\n📋 {ins['executive_summary']}")
    if ins.get("key_findings"):
        for f in ins["key_findings"]: print(f"  • {f}")
    if state["notebook_path"]: print(f"\n📓 {state['notebook_path']}")
    if state["errors"]:
        for e in state["errors"]: print(f"  ❌ {e}")
    return state["final_report"]

def _remaining(state: dict) -> str:
    done = set(s.split("→")[0].strip().split("(")[0].strip() for s in state["steps_taken"])
    seq  = ["run_eda","plan_charts","generate_charts","generate_insights","compile_report"]
    return " → ".join(s for s in seq if s not in done) or "compile_report"

def _hint(name: str, state: dict) -> str:
    hints = {
        "download_url": "URL failed. Try: 1) validate_url to get raw URL, 2) scan_folder for local files.",
        "load_csv":     "File not found. Use scan_folder('.') to discover available files.",
        "train_model":  "Training failed. Ensure target column exists and features are valid.",
        "generate_notebook": "Install: pip install nbformat nbconvert jupyter",
    }
    return hints.get(name, "Previous step failed — try alternative approach or skip.")

# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python data_agent_v3.py "analyze Insurance.csv"')
        sys.exit(1)
    run_agent(" ".join(sys.argv[1:]))