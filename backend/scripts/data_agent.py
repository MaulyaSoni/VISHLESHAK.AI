"""
Vishleshak AI — Data Analysis Agent (Backend v1)
=================================================
Agentic pipeline: URL/path input → full analysis → JSON report + Plotly charts

Usage:
    python data_agent.py --source "path/to/data.csv" --goal "analyze sales trends"
    python data_agent.py --source "https://..." --goal "find top performing regions"

Requirements:
    pip install langchain langgraph langchain-groq plotly pandas numpy pydantic

Optional (observability):
    export LANGCHAIN_TRACING_V2=true
    export LANGCHAIN_API_KEY=your_key
    export LANGCHAIN_PROJECT=vishleshak-data-agent
"""

import argparse
import json
import os
import time
import traceback
from typing import Any, Optional
from io import StringIO

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL_FAST   = "llama-3.1-8b-instant"     # goal extraction, summarizer
MODEL_REASON = "llama-3.3-70b-versatile"  # insight generation
MODEL_JSON   = "openai/gpt-oss-120b"       # structured JSON output

MAX_ROWS_FOR_LLM   = 5        # sample rows sent to LLM
MAX_CHUNK_SIZE     = 10_000   # rows per chunk for large files
MAX_COLS_IN_SCHEMA = 30       # cap schema size

os.environ.setdefault("LANGCHAIN_TRACING_V2",  "false")
os.environ.setdefault("LANGCHAIN_PROJECT",     "vishleshak-data-agent")

# ─────────────────────────────────────────────
#  PYDANTIC SCHEMAS
# ─────────────────────────────────────────────
class GoalSchema(BaseModel):
    business_question: str      = Field(description="Core question to answer")
    target_columns:    list[str]= Field(description="Relevant column names")
    analysis_type:     str      = Field(description="trend|comparison|distribution|correlation|summary")
    success_metric:    str      = Field(description="What a good answer looks like")

class ChartSpec(BaseModel):
    chart_type: str             # bar|line|scatter|histogram|heatmap|box
    x_col:      str
    y_col:      Optional[str]   = None
    color_col:  Optional[str]   = None
    title:      str
    reasoning:  str

class GraphState(BaseModel):
    # inputs
    source:          str        = ""
    user_goal:       str        = ""

    # data
    df_json:         str        = ""      # serialized dataframe
    df_schema:       str        = ""      # column names + dtypes + sample
    row_count:       int        = 0
    col_count:       int        = 0

    # node outputs
    goal:            Optional[GoalSchema]   = None
    preprocess_log:  list[str]              = Field(default_factory=list)
    eda_summary:     dict                   = Field(default_factory=dict)
    chart_specs:     list[ChartSpec]        = Field(default_factory=list)
    charts_json:     list[str]              = Field(default_factory=list)   # plotly JSON
    insights:        str                    = ""
    report:          dict                   = Field(default_factory=dict)

    # control
    errors:          list[str]              = Field(default_factory=list)
    warnings:        list[str]              = Field(default_factory=list)
    current_node:    str                    = ""
    skip_to_report:  bool                   = False

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_client() -> Groq:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set. Run: export GROQ_API_KEY=your_key")
    return Groq(api_key=GROQ_API_KEY)


def groq_call(client: Groq, model: str, prompt: str, retries: int = 3) -> str:
    """Groq call with exponential backoff for rate limits."""
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1024,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < retries - 1:
                wait = 2 ** attempt
                print(f"    ⏳ Rate limit hit, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise e
    return ""


def parse_json_response(raw: str) -> dict:
    import re
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


def build_schema_summary(df: pd.DataFrame) -> str:
    """Compact schema: col names, dtypes, nulls, sample — for LLM context."""
    lines = ["COLUMNS (name | dtype | null% | sample_values)"]
    for col in df.columns[:MAX_COLS_IN_SCHEMA]:
        null_pct = round(df[col].isna().mean() * 100, 1)
        sample   = df[col].dropna().head(3).tolist()
        lines.append(f"  {col} | {df[col].dtype} | {null_pct}% | {sample}")
    lines.append(f"\nSHAPE: {df.shape[0]} rows x {df.shape[1]} cols")
    return "\n".join(lines)


def df_to_json(df: pd.DataFrame) -> str:
    return df.to_json(orient="records", date_format="iso")


def df_from_json(s: str) -> pd.DataFrame:
    return pd.read_json(StringIO(s), orient="records")


# ─────────────────────────────────────────────
#  NODE 0 — FILE VALIDATOR
# ─────────────────────────────────────────────
def file_validator_node(state: GraphState) -> GraphState:
    state.current_node = "file_validator"
    print("📂  [1/7] Validating source...")

    try:
        src = state.source.strip()

        # Google Drive shorthand
        if "drive.google.com" in src and "uc?id=" not in src:
            import re
            fid = re.search(r"/d/([a-zA-Z0-9_-]+)", src)
            if fid:
                src = f"https://drive.google.com/uc?id={fid.group(1)}"

        # Load — chunked for large files
        chunks = []
        reader = pd.read_csv(src, chunksize=MAX_CHUNK_SIZE)
        for i, chunk in enumerate(reader):
            chunks.append(chunk)
            if i == 0:
                print(f"    Loaded chunk 1 ({len(chunk)} rows)...")
            if sum(len(c) for c in chunks) > 200_000:
                state.warnings.append("File >200k rows — using first 200k only.")
                break

        df = pd.concat(chunks, ignore_index=True)

        # Basic checks
        if df.empty:
            state.errors.append("File is empty.")
            state.skip_to_report = True
            return state

        if df.shape[1] < 2:
            state.warnings.append("Only 1 column detected — analysis may be limited.")

        state.df_json    = df_to_json(df)
        state.df_schema  = build_schema_summary(df)
        state.row_count  = df.shape[0]
        state.col_count  = df.shape[1]
        print(f"    ✅ {state.row_count} rows × {state.col_count} cols loaded.")

    except Exception as e:
        state.errors.append(f"File load failed: {str(e)}")
        state.skip_to_report = True

    return state


# ─────────────────────────────────────────────
#  NODE 1 — GOAL AGENT
# ─────────────────────────────────────────────
def goal_node(state: GraphState) -> GraphState:
    state.current_node = "goal"
    print("🎯  [2/7] Extracting goal...")

    client = get_client()
    prompt = f"""You are a data analysis planner.
Given the dataset schema and user goal, return ONLY valid JSON — no markdown.

Schema:
{state.df_schema}

User goal: "{state.user_goal}"

Return exactly:
{{
  "business_question": "<specific question this analysis should answer>",
  "target_columns":    ["<col1>", "<col2>"],
  "analysis_type":     "<trend|comparison|distribution|correlation|summary>",
  "success_metric":    "<what a good answer looks like>"
}}"""

    try:
        raw  = groq_call(client, MODEL_FAST, prompt)
        data = parse_json_response(raw)
        state.goal = GoalSchema(**data)
        print(f"    ✅ Goal: {state.goal.business_question}")
        print(f"    Type: {state.goal.analysis_type} | Cols: {state.goal.target_columns}")
    except Exception as e:
        state.errors.append(f"Goal extraction failed: {e}")
        # Fallback: generic goal
        state.goal = GoalSchema(
            business_question=state.user_goal or "General data analysis",
            target_columns=[],
            analysis_type="summary",
            success_metric="Descriptive statistics and key patterns identified",
        )
        print(f"    ⚠  Using fallback goal.")

    return state


# ─────────────────────────────────────────────
#  NODE 2 — PREPROCESSOR
# ─────────────────────────────────────────────
def preprocess_node(state: GraphState) -> GraphState:
    state.current_node = "preprocess"
    print("🧹  [3/7] Preprocessing data...")

    try:
        df  = df_from_json(state.df_json)
        log = []

        # 1. Drop full-duplicate rows
        before = len(df)
        df.drop_duplicates(inplace=True)
        dropped = before - len(df)
        if dropped:
            log.append(f"Removed {dropped} duplicate rows.")

        # 2. Handle nulls
        null_pct = df.isna().mean()
        high_null_cols = null_pct[null_pct > 0.6].index.tolist()
        if high_null_cols:
            df.drop(columns=high_null_cols, inplace=True)
            log.append(f"Dropped high-null columns (>60%): {high_null_cols}")
            state.warnings.append(f"Columns dropped due to >60% nulls: {high_null_cols}")

        # numeric fill with median, categorical with mode
        for col in df.columns:
            if df[col].isna().sum() == 0:
                continue
            if df[col].dtype in [np.float64, np.int64, float, int]:
                df[col].fillna(df[col].median(), inplace=True)
                log.append(f"Filled nulls in '{col}' with median.")
            else:
                mode_val = df[col].mode()
                if not mode_val.empty:
                    df[col].fillna(mode_val[0], inplace=True)
                    log.append(f"Filled nulls in '{col}' with mode.")

        # 3. Parse date columns
        for col in df.columns:
            if df[col].dtype == object and "date" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    log.append(f"Parsed '{col}' as datetime.")
                except:
                    pass

        # 4. Outlier flag (IQR) — just log, don't remove
        num_cols = df.select_dtypes(include=[np.number]).columns
        for col in num_cols[:5]:
            Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            IQR    = Q3 - Q1
            outliers = ((df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)).sum()
            if outliers > 0:
                log.append(f"'{col}' has {outliers} outliers (IQR method) — kept.")

        state.df_json        = df_to_json(df)
        state.df_schema      = build_schema_summary(df)
        state.row_count      = df.shape[0]
        state.col_count      = df.shape[1]
        state.preprocess_log = log

        print(f"    ✅ {len(log)} preprocessing steps applied.")
        for l in log[:5]:
            print(f"       • {l}")

    except Exception as e:
        state.errors.append(f"Preprocessing error: {e}")

    return state


# ─────────────────────────────────────────────
#  NODE 3 — EDA AGENT
# ─────────────────────────────────────────────
def eda_node(state: GraphState) -> GraphState:
    state.current_node = "eda"
    print("📊  [4/7] Running EDA...")

    try:
        df  = df_from_json(state.df_json)
        eda = {}

        # Descriptive stats (numeric)
        num_df = df.select_dtypes(include=[np.number])
        if not num_df.empty:
            desc = num_df.describe().round(3)
            eda["numeric_summary"] = desc.to_dict()

        # Categorical counts
        cat_df = df.select_dtypes(include=["object", "str", "category"])
        cat_info = {}
        for col in cat_df.columns[:8]:
            vc = df[col].value_counts().head(5)
            cat_info[col] = vc.to_dict()
        if cat_info:
            eda["categorical_counts"] = cat_info

        # Correlations (top 10 pairs)
        if num_df.shape[1] > 1:
            corr = num_df.corr().abs()
            pairs = (
                corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
                .stack()
                .sort_values(ascending=False)
                .head(10)
            )
            eda["top_correlations"] = {str(k): round(v, 3) for k, v in pairs.items()}

        # Missing values summary
        missing = df.isna().sum()
        missing = missing[missing > 0]
        if not missing.empty:
            eda["remaining_missing"] = missing.to_dict()

        # Shape
        eda["shape"] = {"rows": state.row_count, "cols": state.col_count}

        state.eda_summary = eda
        print(f"    ✅ EDA complete — {len(eda)} sections generated.")

    except Exception as e:
        state.errors.append(f"EDA error: {e}")

    return state


# ─────────────────────────────────────────────
#  NODE 4 — SUMMARIZER (cheap model)
# ─────────────────────────────────────────────
def summarizer_node(state: GraphState) -> GraphState:
    state.current_node = "summarizer"
    print("🤖  [5/7] Deciding chart specs  [llama-3.1-8b]...")

    client = get_client()

    eda_text = json.dumps(state.eda_summary, indent=2)[:2000]
    goal_text = state.goal.model_dump() if state.goal else {}

    prompt = f"""You are a data visualization expert.
Given the EDA summary and goal, return ONLY a JSON array of 2-3 chart specs.
No markdown, no explanation.

Goal: {json.dumps(goal_text)}

EDA Summary (truncated):
{eda_text}

Schema:
{state.df_schema[:800]}

Return array like:
[
  {{
    "chart_type": "bar|line|scatter|histogram|heatmap|box",
    "x_col": "<column name>",
    "y_col": "<column name or null>",
    "color_col": "<column name or null>",
    "title": "<chart title>",
    "reasoning": "<why this chart>"
  }}
]

Only use column names that exist in the schema above."""

    try:
        raw   = groq_call(client, MODEL_FAST, prompt)
        raw   = raw.strip()
        if not raw.startswith("["):
            import re
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            raw   = match.group(0) if match else "[]"
        specs = json.loads(raw)
        state.chart_specs = [ChartSpec(**s) for s in specs if s.get("x_col")]
        print(f"    ✅ {len(state.chart_specs)} chart(s) planned.")
    except Exception as e:
        state.errors.append(f"Chart spec generation failed: {e}")
        print(f"    ⚠  Chart planning failed — continuing.")

    return state


# ─────────────────────────────────────────────
#  NODE 5 — VISUALIZER (Plotly tools)
# ─────────────────────────────────────────────
CHART_BUILDERS = {
    "bar":       lambda df, s: px.bar(df,       x=s.x_col, y=s.y_col,   color=s.color_col, title=s.title),
    "line":      lambda df, s: px.line(df,      x=s.x_col, y=s.y_col,   color=s.color_col, title=s.title),
    "scatter":   lambda df, s: px.scatter(df,   x=s.x_col, y=s.y_col,   color=s.color_col, title=s.title),
    "histogram": lambda df, s: px.histogram(df, x=s.x_col,               color=s.color_col, title=s.title),
    "box":       lambda df, s: px.box(df,       x=s.x_col, y=s.y_col,   color=s.color_col, title=s.title),
    "heatmap":   lambda df, s: go.Figure(go.Heatmap(
                     z=df.select_dtypes(include=[np.number]).corr().values,
                     x=df.select_dtypes(include=[np.number]).columns.tolist(),
                     y=df.select_dtypes(include=[np.number]).columns.tolist(),
                 )),
}

def visualizer_node(state: GraphState) -> GraphState:
    state.current_node = "visualizer"
    print("📈  [6/7] Generating charts...")

    if not state.chart_specs:
        print("    ⚠  No chart specs — skipping.")
        return state

    try:
        df = df_from_json(state.df_json)
        charts_json = []

        for spec in state.chart_specs:
            try:
                # validate columns exist
                for col_attr in ["x_col", "y_col", "color_col"]:
                    val = getattr(spec, col_attr)
                    if val and val not in df.columns:
                        setattr(spec, col_attr, None)

                builder = CHART_BUILDERS.get(spec.chart_type, CHART_BUILDERS["bar"])
                fig     = builder(df, spec)
                fig.update_layout(template="plotly_white", margin=dict(l=40, r=40, t=50, b=40))
                charts_json.append(fig.to_json())
                print(f"    ✅ {spec.chart_type.upper()}: {spec.title}")
            except Exception as e:
                state.errors.append(f"Chart '{spec.title}' failed: {e}")
                print(f"    ⚠  Skipped chart: {e}")

        state.charts_json = charts_json

    except Exception as e:
        state.errors.append(f"Visualizer error: {e}")

    return state


# ─────────────────────────────────────────────
#  NODE 6 — INSIGHT AGENT (strong model)
# ─────────────────────────────────────────────
def insight_node(state: GraphState) -> GraphState:
    state.current_node = "insight"
    print("💡  [7/7] Generating insights  [llama-3.3-70b]...")

    client = get_client()

    eda_text  = json.dumps(state.eda_summary, indent=2)[:1500]
    goal_text = state.goal.model_dump() if state.goal else {}
    chart_titles = [s.title for s in state.chart_specs]

    prompt = f"""You are a senior data analyst at a financial consulting firm.
Analyze the EDA results and answer the business question directly.
Return ONLY valid JSON — no markdown.

Business question: {goal_text.get('business_question', state.user_goal)}
Analysis type: {goal_text.get('analysis_type', 'summary')}
Charts generated: {chart_titles}

EDA Summary:
{eda_text}

Preprocessing steps: {state.preprocess_log[:5]}

Return exactly:
{{
  "executive_summary": "<3-4 sentence direct answer to the business question>",
  "key_findings":      ["<finding 1>", "<finding 2>", "<finding 3>"],
  "anomalies":         ["<anomaly or risk 1>", "<anomaly 2>"],
  "recommendations":   ["<action 1>", "<action 2>"],
  "data_quality_note": "<honest note about data limitations>"
}}"""

    try:
        raw  = groq_call(client, MODEL_REASON, prompt)
        data = parse_json_response(raw)
        state.insights = json.dumps(data, indent=2)
        print("    ✅ Insights generated.")
    except Exception as e:
        state.errors.append(f"Insight generation failed: {e}")
        state.insights = json.dumps({"executive_summary": "Insight generation failed.", "error": str(e)})

    return state


# ─────────────────────────────────────────────
#  NODE 7 — REPORT COMPILER
# ─────────────────────────────────────────────
def report_node(state: GraphState) -> GraphState:
    state.current_node = "report"

    insights_dict = {}
    try:
        insights_dict = json.loads(state.insights) if state.insights else {}
    except:
        pass

    state.report = {
        "metadata": {
            "source":     state.source,
            "goal":       state.user_goal,
            "rows":       state.row_count,
            "cols":       state.col_count,
            "timestamp":  pd.Timestamp.now().isoformat(),
        },
        "goal":             state.goal.model_dump() if state.goal else {},
        "preprocessing":    state.preprocess_log,
        "eda_summary":      state.eda_summary,
        "charts_count":     len(state.charts_json),
        "chart_titles":     [s.title for s in state.chart_specs],
        "insights":         insights_dict,
        "warnings":         state.warnings,
        "errors":           state.errors,
    }
    return state


# ─────────────────────────────────────────────
#  CONDITIONAL EDGES
# ─────────────────────────────────────────────
def should_skip(state: GraphState) -> str:
    if state.skip_to_report or state.errors:
        return "skip"
    return "continue"

def check_null_threshold(state: GraphState) -> str:
    """Route to warn node if data quality is too poor for EDA."""
    try:
        df = df_from_json(state.df_json)
        overall_null_pct = df.isna().mean().mean()
        if overall_null_pct > 0.5:
            state.warnings.append(
                f"High overall null rate ({round(overall_null_pct*100,1)}%) "
                "— EDA results may be unreliable."
            )
    except:
        pass
    return "continue"


# ─────────────────────────────────────────────
#  BUILD GRAPH
# ─────────────────────────────────────────────
def build_graph() -> StateGraph:
    g = StateGraph(GraphState)

    g.add_node("file_validator", file_validator_node)
    g.add_node("goal",           goal_node)
    g.add_node("preprocess",     preprocess_node)
    g.add_node("eda",            eda_node)
    g.add_node("summarizer",     summarizer_node)
    g.add_node("visualizer",     visualizer_node)
    g.add_node("insight",        insight_node)
    g.add_node("report",         report_node)

    g.set_entry_point("file_validator")

    g.add_conditional_edges(
        "file_validator",
        should_skip,
        {"skip": "report", "continue": "goal"},
    )

    g.add_edge("goal",       "preprocess")
    g.add_edge("preprocess", "eda")
    g.add_edge("eda",        "summarizer")
    g.add_edge("summarizer", "visualizer")
    g.add_edge("visualizer", "insight")
    g.add_edge("insight",    "report")
    g.add_edge("report",     END)

    return g.compile()


# ─────────────────────────────────────────────
#  MAIN RUNNER
# ─────────────────────────────────────────────
def run_agent(source: str, goal: str) -> dict:
    print(f"\n{'─'*55}")
    print(f"  Vishleshak Data Analysis Agent  |  v1")
    print(f"{'─'*55}")
    print(f"  Source : {source}")
    print(f"  Goal   : {goal}")
    print(f"{'─'*55}\n")

    graph        = build_graph()
    initial_state = GraphState(source=source, user_goal=goal)

    try:
        final = graph.invoke(initial_state)
    except Exception as e:
        print(f"\n❌ Pipeline crashed: {e}")
        traceback.print_exc()
        return {"error": str(e)}

    report = final.get("report", {}) if isinstance(final, dict) else final.report

    print(f"\n{'─'*55}")
    print("  PIPELINE COMPLETE")
    print(f"{'─'*55}")

    insights = report.get("insights", {})
    if insights.get("executive_summary"):
        print(f"\n📋 SUMMARY:\n  {insights['executive_summary']}")

    if insights.get("key_findings"):
        print("\n🔍 KEY FINDINGS:")
        for f in insights["key_findings"]:
            print(f"  • {f}")

    if insights.get("recommendations"):
        print("\n✅ RECOMMENDATIONS:")
        for r in insights["recommendations"]:
            print(f"  → {r}")

    if report.get("warnings"):
        print("\n⚠  WARNINGS:")
        for w in report["warnings"]:
            print(f"  {w}")

    if report.get("errors"):
        print("\n❌ ERRORS:")
        for e in report["errors"]:
            print(f"  {e}")

    print(f"\n  Charts generated: {report.get('charts_count', 0)}")
    print(f"  Titles: {report.get('chart_titles', [])}")
    print(f"{'─'*55}\n")

    # Save charts as HTML files
    charts_json = final.get("charts_json", []) if isinstance(final, dict) else final.charts_json
    for i, cj in enumerate(charts_json):
        import plotly.io as pio
        fig  = pio.from_json(cj)
        path = f"chart_{i+1}.html"
        fig.write_html(path)
        print(f"  💾 Chart saved → {path}")

    # Save full report
    with open("analysis_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  💾 Report saved → analysis_report.json\n")

    return report


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Vishleshak Data Analysis Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python data_agent.py --source data.csv --goal "analyze sales by region"
  python data_agent.py --source https://raw.githubusercontent.com/.../data.csv --goal "find top products"
        """,
    )
    parser.add_argument("--source", required=True,  help="CSV file path or URL")
    parser.add_argument("--goal",   required=True,  help="Analysis goal in plain English")
    args = parser.parse_args()

    run_agent(args.source, args.goal)
