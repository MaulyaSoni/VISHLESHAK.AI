"""
Vishleshak AI — Data Analysis Agent v2
=======================================
True ReAct agent: reads natural language → picks tools → self-corrects → outputs

Usage:
    python data_agent_v2.py "analyze the sales.csv in my data folder"
    python data_agent_v2.py "download iris dataset from https://... and find patterns"
    python data_agent_v2.py "what are the top spending categories in transactions.csv"

Requirements:
    pip install groq plotly pandas numpy pydantic requests

Optional (LangSmith observability):
    export LANGCHAIN_TRACING_V2=true
    export LANGCHAIN_API_KEY=your_key
    export LANGCHAIN_PROJECT=vishleshak-agent-v2
"""

import json
import os
import re
import sys
import time
import traceback
from io import StringIO
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import requests
from groq import Groq

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
GROQ_API_KEY  = os.getenv("GROQ_API_KEY")
MODEL_SUPER   = "llama-3.3-70b-versatile"   # supervisor / ReAct brain
MODEL_FAST    = "llama-3.1-8b-instant"      # chart planning, summarizer
MODEL_INSIGHT = "llama-3.3-70b-versatile"   # final insights

MAX_LOOP_STEPS   = 20      # prevent infinite loops
MAX_CHUNK_ROWS   = 50_000  # chunked load cap
MAX_CHART_RETRY  = 2       # retries per chart on failure

# ─────────────────────────────────────────────
#  AGENT STATE  (simple dict, carried through loop)
# ─────────────────────────────────────────────
def fresh_state(instruction: str) -> dict:
    return {
        "instruction":    instruction,
        "df":             None,       # live DataFrame (not serialized — only in memory)
        "df_schema":      "",
        "source_path":    "",
        "row_count":      0,
        "col_count":      0,
        "preprocess_log": [],
        "eda":            {},
        "chart_specs":    [],
        "charts":         [],         # list of {"title": ..., "fig_json": ..., "path": ...}
        "insights":       {},
        "errors":         [],
        "warnings":       [],
        "steps_taken":    [],
        "done":           False,
        "final_report":   {},
    }

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_client() -> Groq:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set.\nRun: export GROQ_API_KEY=your_key")
    return Groq(api_key=GROQ_API_KEY)


def groq_call(client, model: str, messages: list, tools=None,
              retries: int = 3, max_tokens: int = 2048) -> Any:
    for attempt in range(retries):
        try:
            kwargs = dict(model=model, messages=messages,
                          temperature=0.1, max_tokens=max_tokens)
            if tools:
                kwargs["tools"]       = tools
                kwargs["tool_choice"] = "auto"
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    ⏳ Rate limit — retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def strip_json(raw: str) -> str:
    return re.sub(r"```json|```", "", raw).strip()


def safe_json(raw: str) -> dict | list:
    return json.loads(strip_json(raw))


def build_schema(df: pd.DataFrame, max_cols: int = 25) -> str:
    lines = ["COLUMNS  (name | dtype | null% | top_3_values)"]
    for col in df.columns[:max_cols]:
        null_pct = round(df[col].isna().mean() * 100, 1)
        sample   = df[col].dropna().head(3).tolist()
        lines.append(f"  {col} | {df[col].dtype} | {null_pct}% null | {sample}")
    lines.append(f"\nSHAPE: {df.shape[0]} rows × {df.shape[1]} cols")
    return "\n".join(lines)


def log(state: dict, step: str):
    state["steps_taken"].append(step)
    print(f"  → {step}")


# ─────────────────────────────────────────────
#  TOOLS  (pure functions, called by supervisor)
# ─────────────────────────────────────────────

# ── T1: scan_folder ──────────────────────────
def tool_scan_folder(state: dict, folder: str = ".") -> str:
    """Scan a local folder and return all CSV files found."""
    folder_path = Path(folder)
    if not folder_path.exists():
        return f"Folder '{folder}' does not exist."
    csvs = list(folder_path.rglob("*.csv"))
    if not csvs:
        return f"No CSV files found in '{folder}'."
    result = "\n".join([f"  {p}" for p in csvs[:20]])
    log(state, f"scan_folder('{folder}') → {len(csvs)} CSV(s) found")
    return f"Found {len(csvs)} CSV file(s):\n{result}"


# ── T2: download_url ─────────────────────────
def tool_download_url(state: dict, url: str, save_as: str = "downloaded_data.csv") -> str:
    """Download a CSV from a URL and save locally."""
    try:
        # Handle Google Drive
        if "drive.google.com" in url and "uc?id=" not in url:
            fid = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
            if fid:
                url = f"https://drive.google.com/uc?id={fid.group(1)}&export=download"

        resp = requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()

        total = 0
        with open(save_as, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
                total += len(chunk)
                if total > 200 * 1024 * 1024:
                    state["warnings"].append("File >200MB — download stopped early.")
                    break

        log(state, f"download_url → saved '{save_as}' ({total // 1024}KB)")
        return f"Downloaded and saved as '{save_as}' ({total // 1024} KB)."
    except Exception as e:
        state["errors"].append(f"Download failed: {e}")
        return f"Download failed: {e}"


# ── T3: load_csv ─────────────────────────────
def tool_load_csv(state: dict, path: str) -> str:
    """Load a CSV file into the agent's working dataframe."""
    try:
        chunks, total_rows = [], 0
        for chunk in pd.read_csv(path, chunksize=10_000):
            chunks.append(chunk)
            total_rows += len(chunk)
            if total_rows >= MAX_CHUNK_ROWS:
                state["warnings"].append(f"Large file — using first {MAX_CHUNK_ROWS:,} rows.")
                break

        df = pd.concat(chunks, ignore_index=True)

        if df.empty:
            return "File loaded but is empty."
        if df.shape[1] < 2:
            state["warnings"].append("Only 1 column detected — analysis will be limited.")

        state["df"]          = df
        state["df_schema"]   = build_schema(df)
        state["source_path"] = path
        state["row_count"]   = df.shape[0]
        state["col_count"]   = df.shape[1]

        log(state, f"load_csv('{path}') → {df.shape[0]:,} rows × {df.shape[1]} cols")
        return (f"Loaded '{path}': {df.shape[0]:,} rows × {df.shape[1]} cols.\n"
                f"Schema:\n{state['df_schema']}")
    except Exception as e:
        state["errors"].append(f"CSV load failed: {e}")
        return f"Failed to load '{path}': {e}"


# ── T4: preprocess ───────────────────────────
def tool_preprocess(state: dict) -> str:
    """Clean the loaded dataframe: dedup, null handling, type parsing."""
    if state["df"] is None:
        return "No data loaded. Use load_csv first."
    try:
        df  = state["df"].copy()
        log_entries = []

        # Duplicates
        before = len(df)
        df.drop_duplicates(inplace=True)
        if (d := before - len(df)):
            log_entries.append(f"Removed {d} duplicate rows.")

        # Drop high-null cols
        null_pct = df.isna().mean()
        drop_cols = null_pct[null_pct > 0.6].index.tolist()
        if drop_cols:
            df.drop(columns=drop_cols, inplace=True)
            log_entries.append(f"Dropped high-null cols: {drop_cols}")
            state["warnings"].append(f"Dropped columns (>60% null): {drop_cols}")

        # Fill nulls
        for col in df.columns:
            if df[col].isna().sum() == 0:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].median(), inplace=True)
                log_entries.append(f"Filled '{col}' nulls → median.")
            else:
                mode = df[col].mode()
                if not mode.empty:
                    df[col].fillna(mode[0], inplace=True)
                    log_entries.append(f"Filled '{col}' nulls → mode.")

        # Parse dates
        for col in df.columns:
            if df[col].dtype == object and any(k in col.lower() for k in ["date", "time", "dt"]):
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    log_entries.append(f"Parsed '{col}' → datetime.")
                except:
                    pass

        # Outlier report (IQR)
        for col in df.select_dtypes(include=[np.number]).columns[:5]:
            Q1, Q3 = df[col].quantile([0.25, 0.75])
            IQR = Q3 - Q1
            n = int(((df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)).sum())
            if n:
                log_entries.append(f"'{col}': {n} outliers detected (IQR) — kept.")

        state["df"]           = df
        state["df_schema"]    = build_schema(df)
        state["row_count"]    = df.shape[0]
        state["col_count"]    = df.shape[1]
        state["preprocess_log"] = log_entries

        log(state, f"preprocess → {len(log_entries)} steps")
        return "Preprocessing complete:\n" + "\n".join(f"  • {l}" for l in log_entries)
    except Exception as e:
        state["errors"].append(f"Preprocessing error: {e}")
        return f"Preprocessing failed: {e}"


# ── T5: run_eda ──────────────────────────────
def tool_run_eda(state: dict) -> str:
    """Run exploratory data analysis on the loaded dataframe."""
    if state["df"] is None:
        return "No data loaded."
    try:
        df  = state["df"]
        eda = {}

        # Numeric stats
        num = df.select_dtypes(include=[np.number])
        if not num.empty:
            eda["numeric_summary"] = num.describe().round(3).to_dict()

        # Categorical value counts
        cat = df.select_dtypes(include=["object", "category"])
        cat_info = {}
        for col in cat.columns[:8]:
            cat_info[col] = df[col].value_counts().head(5).to_dict()
        if cat_info:
            eda["categorical_counts"] = cat_info

        # Top correlations
        if num.shape[1] > 1:
            corr = num.corr().abs()
            mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
            pairs = corr.where(mask).stack().sort_values(ascending=False).head(8)
            eda["top_correlations"] = {str(k): round(v, 3) for k, v in pairs.items()}

        # Missing
        missing = df.isna().sum()
        missing = missing[missing > 0]
        if not missing.empty:
            eda["remaining_nulls"] = missing.to_dict()

        eda["shape"] = {"rows": state["row_count"], "cols": state["col_count"]}

        state["eda"] = eda
        log(state, f"run_eda → {len(eda)} sections")

        # Return compact summary for supervisor
        summary_lines = [f"EDA complete ({len(eda)} sections):"]
        if "numeric_summary" in eda:
            cols = list(eda["numeric_summary"].keys())
            summary_lines.append(f"  Numeric cols: {cols}")
        if "categorical_counts" in eda:
            summary_lines.append(f"  Categorical cols: {list(eda['categorical_counts'].keys())}")
        if "top_correlations" in eda:
            top = list(eda["top_correlations"].items())[:3]
            summary_lines.append(f"  Top correlations: {top}")
        return "\n".join(summary_lines)
    except Exception as e:
        state["errors"].append(f"EDA error: {e}")
        return f"EDA failed: {e}"


# ── T6: plan_charts ──────────────────────────
def tool_plan_charts(state: dict, client: Groq) -> str:
    """Ask LLM to decide which 2-3 charts best answer the goal."""
    if not state["eda"]:
        return "Run EDA first."
    try:
        eda_text  = json.dumps(state["eda"], indent=2)[:1800]
        instr     = state["instruction"]
        schema    = state["df_schema"][:800]

        prompt = f"""You are a data viz expert. Return ONLY a JSON array of 2-3 chart specs.
No markdown, no explanation. Use ONLY columns from the schema.

Instruction: "{instr}"
Schema:\n{schema}
EDA:\n{eda_text}

Return:
[{{"chart_type":"bar|line|scatter|histogram|heatmap|box","x_col":"<col>","y_col":"<col or null>","color_col":"<col or null>","title":"<title>","reasoning":"<why>"}}]"""

        resp = groq_call(client, MODEL_FAST, [{"role": "user", "content": prompt}], max_tokens=800)
        raw  = resp.choices[0].message.content.strip()

        # extract JSON array
        if not raw.startswith("["):
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            raw = m.group(0) if m else "[]"

        specs = json.loads(raw)
        # validate columns
        valid_cols = set(state["df"].columns) if state["df"] is not None else set()
        clean = []
        for s in specs:
            if s.get("x_col") not in valid_cols:
                continue
            if s.get("y_col") and s["y_col"] not in valid_cols:
                s["y_col"] = None
            if s.get("color_col") and s["color_col"] not in valid_cols:
                s["color_col"] = None
            clean.append(s)

        state["chart_specs"] = clean
        log(state, f"plan_charts → {len(clean)} chart(s) planned")
        return f"Planned {len(clean)} chart(s): " + ", ".join(s["title"] for s in clean)
    except Exception as e:
        state["errors"].append(f"Chart planning failed: {e}")
        return f"Chart planning failed: {e}"


# ── T7: generate_charts ──────────────────────
BUILDERS = {
    "bar":       lambda df, s: px.bar(df,       x=s["x_col"], y=s.get("y_col"),   color=s.get("color_col"), title=s["title"]),
    "line":      lambda df, s: px.line(df,      x=s["x_col"], y=s.get("y_col"),   color=s.get("color_col"), title=s["title"]),
    "scatter":   lambda df, s: px.scatter(df,   x=s["x_col"], y=s.get("y_col"),   color=s.get("color_col"), title=s["title"]),
    "histogram": lambda df, s: px.histogram(df, x=s["x_col"],                     color=s.get("color_col"), title=s["title"]),
    "box":       lambda df, s: px.box(df,       x=s["x_col"], y=s.get("y_col"),   color=s.get("color_col"), title=s["title"]),
    "heatmap":   lambda df, s: go.Figure(go.Heatmap(
                     z=df.select_dtypes(include=[np.number]).corr().round(2).values,
                     x=df.select_dtypes(include=[np.number]).columns.tolist(),
                     y=df.select_dtypes(include=[np.number]).columns.tolist(),
                     colorscale="Blues", zmin=-1, zmax=1,
                 ), layout=go.Layout(title=s["title"])),
}

def tool_generate_charts(state: dict) -> str:
    """Generate all planned charts as Plotly HTML files."""
    if not state["chart_specs"]:
        return "No chart specs. Run plan_charts first."
    if state["df"] is None:
        return "No data loaded."

    df      = state["df"]
    results = []

    for spec in state["chart_specs"]:
        title = spec["title"]
        success = False

        for attempt in range(MAX_CHART_RETRY + 1):
            try:
                builder = BUILDERS.get(spec["chart_type"], BUILDERS["bar"])
                fig     = builder(df, spec)
                fig.update_layout(
                    template="plotly_white",
                    margin=dict(l=50, r=50, t=60, b=50),
                    font=dict(family="Inter, sans-serif"),
                )
                path = f"chart_{len(state['charts']) + 1}_{re.sub(r'[^a-z0-9]', '_', title.lower())[:30]}.html"
                fig.write_html(path)

                state["charts"].append({
                    "title":    title,
                    "type":     spec["chart_type"],
                    "fig_json": fig.to_json(),
                    "path":     path,
                    "spec":     spec,
                })
                results.append(f"✅ {spec['chart_type'].upper()}: {title} → {path}")
                success = True
                break

            except Exception as e:
                if attempt < MAX_CHART_RETRY:
                    # Self-correction: fallback to histogram on the first numeric col
                    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    if num_cols:
                        spec = {**spec, "chart_type": "histogram", "x_col": num_cols[0], "y_col": None}
                        results.append(f"  ⚠ Retry {attempt+1}: fallback to histogram on '{num_cols[0]}'")
                else:
                    state["errors"].append(f"Chart '{title}' failed after {MAX_CHART_RETRY} retries: {e}")
                    results.append(f"❌ SKIPPED: {title} — {e}")

    log(state, f"generate_charts → {len(state['charts'])} chart(s) saved")
    return "\n".join(results)


# ── T8: generate_insights ────────────────────
def tool_generate_insights(state: dict, client: Groq) -> str:
    """Generate deep insights using EDA + chart context + original instruction."""
    if not state["eda"]:
        return "No EDA results. Run run_eda first."
    try:
        eda_text     = json.dumps(state["eda"], indent=2)[:1600]
        chart_context = "\n".join(
            f"  Chart: '{c.get('title', 'Untitled')}' ({c.get('type', 'unknown')}) — x={c.get('spec', {}).get('x_col')}, y={c.get('spec', {}).get('y_col')}"
            for c in state["charts"]
        ) or "  No charts generated."
        preprocess = "\n".join(f"  • {l}" for l in state["preprocess_log"][:6])

        prompt = f"""You are a senior financial data analyst.
Answer the user's instruction with direct, specific findings from the data.
Return ONLY valid JSON — no markdown.

User instruction: "{state['instruction']}"

Dataset: {state['row_count']:,} rows × {state['col_count']} cols
Schema:\n{state['df_schema'][:600]}

EDA results:\n{eda_text}

Charts generated:\n{chart_context}

Preprocessing done:\n{preprocess}

Return exactly:
{{
  "executive_summary":  "<3-4 sentences directly answering the instruction with specific numbers>",
  "key_findings":       ["<finding with specific stat>", "<finding>", "<finding>"],
  "anomalies_or_risks": ["<anomaly 1>", "<anomaly 2>"],
  "recommendations":    ["<specific action 1>", "<specific action 2>"],
  "chart_interpretation": {{
    "<chart title>": "<1-2 sentence interpretation of what this chart reveals>"
  }},
  "data_quality_note":  "<honest limitations of this dataset>"
}}"""

        resp = groq_call(client, MODEL_INSIGHT,
                         [{"role": "user", "content": prompt}], max_tokens=1500)
        raw  = resp.choices[0].message.content.strip()
        data = safe_json(raw)
        state["insights"] = data

        log(state, "generate_insights → complete")
        return f"Insights generated. Summary: {data.get('executive_summary', '')[:120]}..."
    except Exception as e:
        state["errors"].append(f"Insights failed: {e}")
        return f"Insight generation failed: {e}"


# ── T9: compile_report ───────────────────────
def tool_compile_report(state: dict) -> str:
    """Compile everything into final JSON report + print summary."""
    report = {
        "metadata": {
            "instruction":  state["instruction"],
            "source":       state["source_path"],
            "rows":         state["row_count"],
            "cols":         state["col_count"],
            "timestamp":    pd.Timestamp.now().isoformat(),
            "steps_taken":  state["steps_taken"],
        },
        "preprocessing":     state["preprocess_log"],
        "eda_summary":       state["eda"],
        "charts": [{"title": c.get("title", "Untitled"), "type": c.get("type", "unknown"), "path": c.get("path", "")}
                   for c in state["charts"]],
        "insights":          state["insights"],
        "warnings":          state["warnings"],
        "errors":            state["errors"],
    }
    state["final_report"] = report
    state["done"]         = True

    with open("analysis_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    log(state, "compile_report → analysis_report.json saved")
    return "Report compiled and saved → analysis_report.json"


# ─────────────────────────────────────────────
#  TOOL REGISTRY  (what the supervisor sees)
# ─────────────────────────────────────────────
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "scan_folder",
            "description": "Scan a local folder to find available CSV files. Use when user mentions a folder or doesn't specify a file name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder": {"type": "string", "description": "Folder path to scan. Default '.' for current directory."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_url",
            "description": "Download a CSV file from a URL (GitHub, Google Drive, Kaggle direct links, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "url":     {"type": "string", "description": "Direct URL to the CSV file"},
                    "save_as": {"type": "string", "description": "Local filename to save as. Default: downloaded_data.csv"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "load_csv",
            "description": "Load a CSV file into memory for analysis. Use after scan_folder or download_url.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Local path to the CSV file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "preprocess",
            "description": "Clean the loaded data: remove duplicates, handle nulls, parse dates, flag outliers.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_eda",
            "description": "Run exploratory data analysis: descriptive stats, correlations, value counts.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plan_charts",
            "description": "Decide which 2-3 charts best visualize the data for the user's goal.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_charts",
            "description": "Generate and save all planned charts as interactive HTML files.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_insights",
            "description": "Generate deep analytical insights from EDA and charts, answering the user's question.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compile_report",
            "description": "Compile all results into a final JSON report. Call this LAST when all analysis is done.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
]

# ─────────────────────────────────────────────
#  TOOL DISPATCHER
# ─────────────────────────────────────────────
def dispatch(tool_name: str, tool_args: dict, state: dict, client: Groq) -> str:
    print(f"\n  🔧 [{tool_name}]")
    try:
        if tool_name == "scan_folder":
            return tool_scan_folder(state, tool_args.get("folder", "."))
        elif tool_name == "download_url":
            return tool_download_url(state, tool_args["url"], tool_args.get("save_as", "downloaded_data.csv"))
        elif tool_name == "load_csv":
            return tool_load_csv(state, tool_args["path"])
        elif tool_name == "preprocess":
            return tool_preprocess(state)
        elif tool_name == "run_eda":
            return tool_run_eda(state)
        elif tool_name == "plan_charts":
            return tool_plan_charts(state, client)
        elif tool_name == "generate_charts":
            return tool_generate_charts(state)
        elif tool_name == "generate_insights":
            return tool_generate_insights(state, client)
        elif tool_name == "compile_report":
            return tool_compile_report(state)
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        err = f"Tool '{tool_name}' crashed: {e}"
        state["errors"].append(err)
        traceback.print_exc()
        return err


# ─────────────────────────────────────────────
#  REACT SUPERVISOR LOOP
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are Vishleshak, an autonomous data analysis agent.
Your job is to fully analyze a dataset and answer the user's instruction.

You have these tools available:
  scan_folder, download_url, load_csv, preprocess, run_eda,
  plan_charts, generate_charts, generate_insights, compile_report

Standard workflow:
1. If no file path given → scan_folder to find CSVs, then load_csv
2. If URL given → download_url, then load_csv
3. If path given directly → load_csv
4. Always run: preprocess → run_eda → plan_charts → generate_charts → generate_insights → compile_report

Rules:
- Never skip preprocessing or EDA
- Always generate at least 2 charts
- Always call compile_report as the final step
- If a tool returns an error, adapt and continue — do not stop
- Call tools one at a time and wait for results
"""

def run_agent(instruction: str) -> dict:
    print(f"\n{'═'*58}")
    print(f"  Vishleshak Data Agent  v2  |  ReAct Mode")
    print(f"{'═'*58}")
    print(f"  Instruction: {instruction}")
    print(f"{'═'*58}\n")

    client   = get_client()
    state    = fresh_state(instruction)
    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": instruction},
    ]

    for step in range(MAX_LOOP_STEPS):
        print(f"\n⟳  Step {step + 1}/{MAX_LOOP_STEPS}")

        resp = groq_call(client, MODEL_SUPER, messages,
                         tools=TOOL_SCHEMAS, max_tokens=1024)
        msg  = resp.choices[0].message

        # ── No tool call = supervisor decided to respond in text ──
        if not msg.tool_calls:
            final_text = msg.content or ""
            print(f"\n  💬 Agent: {final_text}")
            messages.append({"role": "assistant", "content": final_text})

            # If report was compiled we're done; otherwise push agent to continue
            if state["done"]:
                break
            else:
                messages.append({
                    "role":    "user",
                    "content": "Continue — call compile_report if analysis is complete, otherwise proceed with next step."
                })
            continue

        # ── Tool calls ──
        tool_call  = msg.tool_calls[0]
        tool_name  = tool_call.function.name
        tool_args  = json.loads(tool_call.function.arguments or "{}")

        # Append assistant message with tool call
        messages.append({
            "role":       "assistant",
            "content":    None,
            "tool_calls": [{
                "id":       tool_call.id,
                "type":     "function",
                "function": {"name": tool_name, "arguments": json.dumps(tool_args)},
            }]
        })

        # Execute tool
        tool_result = dispatch(tool_name, tool_args, state, client)
        print(f"     Result: {str(tool_result)[:200]}")

        # Append tool result to message history
        messages.append({
            "role":         "tool",
            "tool_call_id": tool_call.id,
            "content":      str(tool_result),
        })

        # Exit if done
        if state["done"]:
            print(f"\n  ✅ Agent marked done after '{tool_name}'")
            break

    # ─────────────────────────────────────────
    #  PRINT FINAL SUMMARY
    # ─────────────────────────────────────────
    report   = state["final_report"]
    insights = state["insights"]

    print(f"\n{'═'*58}")
    print("  ANALYSIS COMPLETE")
    print(f"{'═'*58}")

    if insights.get("executive_summary"):
        print(f"\n📋 SUMMARY\n  {insights['executive_summary']}")

    if insights.get("key_findings"):
        print("\n🔍 KEY FINDINGS")
        for f in insights["key_findings"]:
            print(f"  • {f}")

    if insights.get("recommendations"):
        print("\n✅ RECOMMENDATIONS")
        for r in insights["recommendations"]:
            print(f"  → {r}")

    if insights.get("chart_interpretation"):
        print("\n📊 CHART INTERPRETATIONS")
        for title, interp in insights["chart_interpretation"].items():
            print(f"  [{title}]\n    {interp}")

    if state["warnings"]:
        print("\n⚠  WARNINGS")
        for w in state["warnings"]:
            print(f"  {w}")

    if state["errors"]:
        print("\n❌ ERRORS")
        for e in state["errors"]:
            print(f"  {e}")

    print(f"\n  Steps taken   : {len(state['steps_taken'])}")
    print(f"  Charts saved  : {len(state['charts'])}")
    for c in state["charts"]:
        print(f"    → {c['path']}")
    print(f"  Report saved  : analysis_report.json")
    print(f"{'═'*58}\n")

    return report


# ─────────────────────────────────────────────
#  CLI ENTRY
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage:")
        print('  python data_agent_v2.py "analyze the sales.csv in my data folder"')
        print('  python data_agent_v2.py "download from https://... and summarize"')
        print('  python data_agent_v2.py "what are spending patterns in transactions.csv"')
        sys.exit(1)

    instruction = " ".join(sys.argv[1:])
    run_agent(instruction)