"""
LangGraph Supervisor Graph - Core Orchestration Layer
Simplified version with sequential execution fallback
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import uuid

import pandas as pd

logger = logging.getLogger("vishleshak.supervisor")


class VishleshakState(TypedDict):
    user_id: str
    session_id: str
    domain: str
    user_query: str
    dataset: Optional[pd.DataFrame]
    dataset_meta: dict
    analysis_result: dict
    charts: list
    insights_text: str
    pdf_path: Optional[str]
    memory_context: str
    proactive_flags: list
    agent_trace: list
    next_agent: str
    error: Optional[str]
    dataset_name: Optional[str]
    pdf_trigger: Optional[str]


def memory_agent(state: VishleshakState) -> VishleshakState:
    """Memory Agent - Loads and writes summarized memory using 3-tier system"""
    logger.info("Memory agent processing...")
    
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id")
    domain = state.get("domain", "general")
    dataset = state.get("dataset")
    
    try:
        from core.memory_v2 import get_memory_manager
        mm = get_memory_manager(user_id=user_id, domain=domain)
        
        dataset_hash = ""
        if dataset is not None:
            import hashlib
            col_str = ",".join(sorted(dataset.columns.tolist()))
            dataset_hash = hashlib.md5(col_str.encode()).hexdigest()[:12]
            state["dataset_hash"] = dataset_hash
        
        columns = list(dataset.columns) if dataset is not None else []
        
        ctx = mm.load_context(dataset_hash=dataset_hash, columns=columns)
        state["memory_context"] = ctx
        
    except Exception as e:
        logger.warning(f"Memory load error: {e}")
        state["memory_context"] = ""
    
    return state


def intent_router(state: VishleshakState) -> VishleshakState:
    """Classifies user query and sets domain with intelligent routing"""
    logger.info("Intent router processing...")
    
    query = state.get("user_query", "")
    current_domain = state.get("domain", "general")
    
    # Auto-detect domain from dataset columns if available
    meta = state.get("dataset_meta", {})
    if meta:
        columns = list(meta.get("dtypes", {}).keys())
        if columns:
            col_str = " ".join(columns).lower()
            
            finance_kw = ["revenue", "profit", "loss", "sales", "income", "expense", "cost", "asset", "liability", "cash", "margin"]
            insurance_kw = ["claim", "premium", "policy", "coverage", "risk", "policyholder", "lapse", "underwriting"]
            ecommerce_kw = ["order", "customer", "cart", "churn", "basket", "return", "sku", "product", "basket"]
            
            for kw in finance_kw:
                if kw in col_str:
                    current_domain = "finance"
                    break
            else:
                for kw in insurance_kw:
                    if kw in col_str:
                        current_domain = "insurance"
                        break
                else:
                    for kw in ecommerce_kw:
                        if kw in col_str:
                            current_domain = "ecommerce"
                            break
    
    # Try to use LLM for domain detection
    if query and len(query) > 5:
        try:
            from core.llm import get_chat_llm
            llm = get_chat_llm()
            
            if llm:
                routing_prompt = f"""Analyze this user query and determine the appropriate domain.

Query: {query}

Return ONLY a JSON object like: {{"domain": "finance"|"insurance"|"ecommerce"|"general", "intent": "brief description of what user wants"}}

Consider:
- finance: revenue, profit, loss, expenses, cash flow, margins
- insurance: claims, premiums, policies, risk, coverage
- ecommerce: customers, orders, products, churn, baskets"""

                try:
                    response = llm.invoke(routing_prompt)
                    response_text = response.content if hasattr(response, 'content') else str(response)
                    
                    # Parse response
                    if "finance" in response_text.lower():
                        current_domain = "finance"
                    elif "insurance" in response_text.lower():
                        current_domain = "insurance"
                    elif "ecommerce" in response_text.lower():
                        current_domain = "ecommerce"
                    
                    logger.info(f"LLM detected domain: {current_domain}")
                except:
                    pass
        except:
            pass
    
    state["domain"] = current_domain
    state["next_agent"] = "data_agent"
    state["agent_trace"].append({
        "node": "intent_router", 
        "domain": current_domain,
        "query": query[:50] if query else ""
    })
    
    return state


def data_agent(state: VishleshakState) -> VishleshakState:
    """Data Agent - Handles profiling, cleaning, statistical analysis"""
    logger.info("Data agent processing...")
    
    df = state.get("dataset")
    if df is None:
        state["error"] = "No dataset available"
        state["next_agent"] = "END"
        return state
    
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        profile = {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_count": len(numeric_cols),
            "categorical_count": len(cat_cols),
            "missing_cells": int(df.isnull().sum().sum()),
            "missing_pct": round(df.isnull().sum().sum() / max(1, df.shape[0] * df.shape[1]) * 100, 2),
            "duplicates": int(df.duplicated().sum()),
            "numeric_columns": numeric_cols[:10],
            "categorical_columns": cat_cols[:10]
        }
        
        df_clean = df.copy()
        for col in df_clean.columns:
            if df_clean[col].dtype in ['object', 'category']:
                df_clean[col] = df_clean[col].fillna("Unknown")
            elif pd.api.types.is_numeric_dtype(df_clean[col]):
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
        
        stats = {}
        for col in numeric_cols:
            stats[col] = {
                "mean": float(df_clean[col].mean()),
                "median": float(df_clean[col].median()),
                "std": float(df_clean[col].std()),
                "min": float(df_clean[col].min()),
                "max": float(df_clean[col].max()),
            }
        
        state["dataset"] = df_clean
        state["dataset_meta"] = {
            "profile": profile,
            "dtypes": df_clean.dtypes.astype(str).to_dict(),
            "shape": df_clean.shape,
            "statistics": stats,
            "cleaning_applied": True
        }
        state["analysis_result"] = {
            "profile": profile,
            "statistics": stats,
            "data_agent_completed": True
        }
        
        logger.info(f"Data agent completed: {profile['rows']} rows, {profile['columns']} cols")
    
    except Exception as e:
        logger.error(f"Data agent error: {e}")
        state["error"] = str(e)
    
    state["agent_trace"].append({"node": "data_agent"})
    state["next_agent"] = "insight_agent"
    
    # Generate proactive flags for pattern analysis
    try:
        from agentic_core.proactive_engine import generate_proactive_flags
        df = state.get("dataset")
        if df is not None:
            flags = generate_proactive_flags(df)
            state["proactive_flags"] = flags
            logger.info(f"Generated {len(flags)} proactive flags")
    except Exception as e:
        logger.warning(f"Proactive flag generation failed: {e}")
        state["proactive_flags"] = []
    
    return state


def insight_agent(state: VishleshakState) -> VishleshakState:
    """Insight Agent - Generates LLM narratives with domain-specific analysis"""
    logger.info("Insight agent processing...")
    
    df = state.get("dataset")
    meta = state.get("dataset_meta", {})
    domain = state.get("domain", "general")
    
    try:
        from core.llm import get_chat_llm
        llm = get_chat_llm()
        
        if llm:
            profile = meta.get("profile", {})
            shape = meta.get("shape", [0, 0])
            stats = meta.get("statistics", {})
            
            # Build domain-specific analysis prompt
            domain_focus = {
                "finance": "Focus on revenue trends, expense ratios, cash flow, profit margins, and financial risk indicators.",
                "insurance": "Focus on loss ratios, claim frequency, premium adequacy, IRDAI compliance, and risk segmentation.",
                "ecommerce": "Focus on customer churn, basket size, return rates, cohort retention, and seasonal demand patterns.",
                "general": "Focus on data quality, descriptive statistics, correlations, patterns, and anomalies."
            }
            
            focus = domain_focus.get(domain, domain_focus["general"])
            
            # Get top stats for context
            top_stats = []
            for col, col_stats in list(stats.items())[:5]:
                top_stats.append(f"{col}: mean={col_stats.get('mean', 0):.2f}, std={col_stats.get('std', 0):.2f}")
            
            prompt = f"""You are Vishleshak AI, an expert domain data analyst.

DOMAIN: {domain}
{focus}

Data Profile:
- Rows: {shape[0]}, Columns: {shape[1]}
- Numeric columns: {profile.get('numeric_count', 0)}
- Categorical columns: {profile.get('categorical_count', 0)}
- Missing values: {profile.get('missing_pct', 0)}%
- Duplicate rows: {profile.get('duplicates', 0)}

Key Statistics:
{chr(10).join(top_stats)}

Generate a comprehensive analytical narrative (300-500 words) that:
1. Identifies the main patterns and trends in the data
2. Notes any data quality issues or anomalies
3. Provides domain-specific insights relevant to {domain}
4. Suggests areas for further analysis
5. Highlights any surprising findings

Write in a professional, analytical tone."""

            try:
                from langchain_core.output_parsers import StrOutputParser
                chain = llm | StrOutputParser()
                narrative = chain.invoke(prompt)
                state["insights_text"] = narrative
            except Exception as e:
                logger.warning(f"LLM failed: {e}")
                state["insights_text"] = _generate_fallback_insights(profile, stats, domain)
        else:
            state["insights_text"] = _generate_fallback_insights(profile, stats, domain)
    except Exception as e:
        logger.warning(f"Insight agent error: {e}")
        state["insights_text"] = "Analysis completed. Enable LLM for detailed insights."
    
    state["agent_trace"].append({"node": "insight_agent", "domain": domain})
    state["next_agent"] = "viz_agent"
    
    return state


def _generate_fallback_insights(profile: dict, stats: dict, domain: str) -> str:
    """Generate basic insights without LLM."""
    rows = profile.get("rows", 0)
    cols = profile.get("columns", 0)
    missing = profile.get("missing_pct", 0)
    duplicates = profile.get("duplicates", 0)
    numeric = profile.get("numeric_count", 0)
    categorical = profile.get("categorical_count", 0)
    
    insights = [f"Dataset contains {rows:,} rows and {cols} columns."]
    insights.append(f"Numeric columns: {numeric}, Categorical columns: {categorical}.")
    
    if missing > 10:
        insights.append(f"Warning: {missing}% missing values detected. Consider data cleaning.")
    else:
        insights.append(f"Data quality is good with only {missing}% missing values.")
    
    if duplicates > 0:
        insights.append(f"Found {duplicates} duplicate rows that may need removal.")
    
    # Domain-specific observations
    if domain == "finance":
        insights.append("Financial analysis: Review revenue and expense columns for trends.")
    elif domain == "insurance":
        insights.append("Insurance analysis: Check claim and premium columns for ratio analysis.")
    elif domain == "ecommerce":
        insights.append("E-commerce analysis: Monitor customer behavior patterns.")
    
    return " ".join(insights)


def viz_agent(state: VishleshakState) -> VishleshakState:
    """Viz Agent - Plotly chart generation with multiple chart types"""
    logger.info("Viz agent processing...")
    
    df = state.get("dataset")
    if df is None:
        state["next_agent"] = "report_agent"
        return state
    
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        
        charts = []
        output_dir = os.path.join("data", "charts")
        os.makedirs(output_dir, exist_ok=True)
        
        session_id = state.get("session_id", "default")
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Chart 1: Histogram for first numeric column
        if len(numeric_cols) >= 1:
            try:
                fig = px.histogram(df, x=numeric_cols[0], nbins=30, 
                                 title=f"Distribution of {numeric_cols[0]}",
                                 color_discrete_sequence=['#6366F1'])
                fig.update_layout(template="plotly_white", font=dict(size=10))
                chart_path = os.path.join(output_dir, f"chart_{session_id}_hist1.png")
                fig.write_image(chart_path, width=800, height=400)
                charts.append(chart_path)
                logger.info(f"Generated histogram: {numeric_cols[0]}")
            except Exception as e:
                logger.warning(f"Histogram failed: {e}")
        
        # Chart 2: Scatter plot for first two numeric columns
        if len(numeric_cols) >= 2:
            try:
                fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], 
                                title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
                                color_discrete_sequence=['#10B981'])
                fig.update_layout(template="plotly_white")
                chart_path = os.path.join(output_dir, f"chart_{session_id}_scatter.png")
                fig.write_image(chart_path, width=800, height=400)
                charts.append(chart_path)
            except Exception as e:
                logger.warning(f"Scatter failed: {e}")
        
        # Chart 3: Bar chart for categorical vs numeric
        if len(cat_cols) >= 1 and len(numeric_cols) >= 1:
            try:
                grouped = df.groupby(cat_cols[0])[numeric_cols[0]].mean().reset_index()
                if len(grouped) <= 20:  # Only show if not too many categories
                    fig = px.bar(grouped, x=cat_cols[0], y=numeric_cols[0], 
                               title=f"Average {numeric_cols[0]} by {cat_cols[0]}",
                               color_discrete_sequence=['#F59E0B'])
                    fig.update_layout(template="plotly_white")
                    chart_path = os.path.join(output_dir, f"chart_{session_id}_bar.png")
                    fig.write_image(chart_path, width=800, height=400)
                    charts.append(chart_path)
            except Exception as e:
                logger.warning(f"Bar chart failed: {e}")
        
        # Chart 4: Box plot for distribution analysis
        if len(numeric_cols) >= 2:
            try:
                fig = px.box(df, y=numeric_cols[:4], title="Distribution Comparison (Box Plot)",
                            color_discrete_sequence=['#6366F1', '#10B981', '#F59E0B', '#EF4444'])
                fig.update_layout(template="plotly_white")
                chart_path = os.path.join(output_dir, f"chart_{session_id}_box.png")
                fig.write_image(chart_path, width=800, height=400)
                charts.append(chart_path)
            except Exception as e:
                logger.warning(f"Box plot failed: {e}")
        
        # Chart 5: Correlation heatmap
        if len(numeric_cols) >= 3:
            try:
                corr = df[numeric_cols[:6]].corr()
                fig = px.imshow(corr, text_auto=True, aspect="auto",
                               title="Correlation Heatmap",
                               color_continuous_scale="RdBu_r")
                fig.update_layout(template="plotly_white")
                chart_path = os.path.join(output_dir, f"chart_{session_id}_corr.png")
                fig.write_image(chart_path, width=800, height=400)
                charts.append(chart_path)
            except Exception as e:
                logger.warning(f"Heatmap failed: {e}")
        
        # Chart 6: Pie chart for categorical distribution
        if len(cat_cols) >= 1:
            try:
                cat_counts = df[cat_cols[0]].value_counts().head(10)
                if len(cat_counts) <= 10 and len(cat_counts) > 1:
                    fig = px.pie(values=cat_counts.values, names=cat_counts.index,
                                title=f"Distribution: {cat_cols[0]}")
                    fig.update_layout(template="plotly_white")
                    chart_path = os.path.join(output_dir, f"chart_{session_id}_pie.png")
                    fig.write_image(chart_path, width=800, height=400)
                    charts.append(chart_path)
            except Exception as e:
                logger.warning(f"Pie chart failed: {e}")
        
        # Chart 7: Second numeric column histogram
        if len(numeric_cols) >= 2:
            try:
                fig = px.histogram(df, x=numeric_cols[1], nbins=30,
                                 title=f"Distribution of {numeric_cols[1]}",
                                 color_discrete_sequence=['#10B981'])
                fig.update_layout(template="plotly_white")
                chart_path = os.path.join(output_dir, f"chart_{session_id}_hist2.png")
                fig.write_image(chart_path, width=800, height=400)
                charts.append(chart_path)
            except Exception as e:
                logger.warning(f"Second histogram failed: {e}")
        
        state["charts"] = charts
        logger.info(f"Viz agent: Generated {len(charts)} charts: {[os.path.basename(c) for c in charts]}")
    
    except Exception as e:
        logger.warning(f"Viz agent error: {e}")
        state["charts"] = []
    
    state["agent_trace"].append({"node": "viz_agent", "charts": len(state.get("charts", []))})
    state["next_agent"] = "report_agent"
    
    return state


def report_agent(state: VishleshakState) -> VishleshakState:
    """Report Agent - Triggers PDF subgraph and saves memory"""
    logger.info("Report agent processing...")
    
    # Save analysis to memory (Tier 2)
    try:
        from core.memory_v2 import get_memory_manager
        mm = get_memory_manager(user_id=state.get("user_id", "default"), domain=state.get("domain", "general"))
        mm.save_analysis(state)
    except Exception as e:
        logger.warning(f"Memory save error: {e}")
    
    try:
        from tools.specialized.pdf_subgraph import generate_pdf_report
        
        trigger = state.get("pdf_trigger", "auto")
        pdf_path = generate_pdf_report(state=state, mode=trigger)
        state["pdf_path"] = pdf_path
        logger.info(f"PDF report generated: {pdf_path}")
    except Exception as e:
        logger.warning(f"PDF generation skipped: {e}")
        state["pdf_path"] = None
    
    state["agent_trace"].append({"node": "report_agent"})
    state["next_agent"] = "END"
    
    return state


def invoke_supervisor(
    user_query: str,
    dataset: Optional[pd.DataFrame] = None,
    user_id: str = "default",
    session_id: Optional[str] = None,
    domain: str = "general",
    file_path: Optional[str] = None,
    file_mode: str = "path"
) -> VishleshakState:
    """Invoke the supervisor - sequential execution"""
    
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    if dataset is None and file_path:
        try:
            from tools.custom_tools.file_access_tool import load_dataset
            dataset, meta = load_dataset(file_path, mode=file_mode, user_id=user_id)
        except Exception as e:
            logger.warning(f"Failed to load file: {e}")
    
    dataset_name = f"data_{session_id[:8]}"
    
    state = VishleshakState(
        user_id=user_id,
        session_id=session_id,
        domain=domain,
        user_query=user_query,
        dataset=dataset,
        dataset_meta={},
        analysis_result={},
        charts=[],
        insights_text="",
        pdf_path=None,
        memory_context="",
        proactive_flags=[],
        agent_trace=[],
        next_agent="data_agent",
        error=None,
        dataset_name=dataset_name,
        pdf_trigger="auto"
    )
    
    # Sequential execution
    logger.info("Starting sequential supervisor execution")
    
    state = memory_agent(state)
    state = intent_router(state)
    state = data_agent(state)
    state = insight_agent(state)
    state = viz_agent(state)
    state = report_agent(state)
    
    logger.info("Supervisor execution complete")
    
    return state


def get_supervisor_graph():
    """Return the supervisor graph (for compatibility)."""
    return invoke_supervisor