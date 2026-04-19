"""
Intelligent Dashboard Visualizer for Vishleshak AI v1
Claude-level smart chart selection — picks the RIGHT chart for every data type.

Returns List[Tuple[str, go.Figure]] so the caller can label each panel.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

PALETTE = dict(
    primary="#4F46E5", secondary="#7C3AED", accent="#06B6D4",
    success="#10B981", warning="#F59E0B", danger="#EF4444", neutral="#6B7280"
)
SEQ   = px.colors.sequential.Plasma
DIV   = px.colors.diverging.RdBu
QUAL  = ["#4F46E5","#06B6D4","#10B981","#F59E0B","#EF4444","#8B5CF6","#EC4899","#14B8A6"]

_BASE = dict(
    template="plotly_white",
    font=dict(family="Inter, system-ui, sans-serif", size=13, color="#1F2937"),
    title_font=dict(size=17, color="#111827", family="Inter, system-ui, sans-serif"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(248,250,252,1)",
    margin=dict(t=65, b=55, l=65, r=35),
    hoverlabel=dict(bgcolor="white", bordercolor="#E5E7EB",
                    font_size=13, font_family="Inter, system-ui, sans-serif"),
)

def _style(fig: go.Figure, height: int = 480) -> go.Figure:
    fig.update_layout(height=height, **_BASE)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#F3F4F6",
                     showline=True, linewidth=1, linecolor="#E5E7EB", tickfont_size=11)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#F3F4F6",
                     showline=False, tickfont_size=11)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# SMART CHART BUILDERS  (one method → one chart, always richly annotated)
# ─────────────────────────────────────────────────────────────────────────────

def _histogram_stats(df: pd.DataFrame, col: str) -> go.Figure:
    """Histogram + mean/median lines + full stats footer."""
    data = df[col].dropna()
    mean, median, std = data.mean(), data.median(), data.std()
    skew, kurt = data.skew(), data.kurtosis()
    q1, q3 = data.quantile(0.25), data.quantile(0.75)

    nbins = min(50, max(10, len(data) // 20))
    fig = go.Figure(go.Histogram(
        x=data, nbinsx=nbins, name="Frequency",
        marker=dict(color=PALETTE["primary"], opacity=0.8, line=dict(width=0.5, color="white")),
        hovertemplate="<b>%{x:.2f}</b><br>Count: %{y}<extra></extra>"
    ))

    for val, label, clr in [(mean, f"Mean {mean:.2f}", PALETTE["danger"]),
                             (median, f"Median {median:.2f}", PALETTE["success"])]:
        fig.add_vline(x=val, line=dict(color=clr, width=2.5, dash="dash"),
                      annotation=dict(text=label, font=dict(size=11, color=clr),
                                      yref="paper", y=0.96))

    shape_desc = ("right-skewed" if skew > 0.5 else "left-skewed" if skew < -0.5 else "approx. normal")
    footer = (f"n={len(data):,}  ·  mean={mean:.2f}  ·  median={median:.2f}  ·  σ={std:.2f}"
              f"  ·  IQR={q3-q1:.2f}  ·  skew={skew:.2f} ({shape_desc})")
    fig.add_annotation(text=footer, xref="paper", yref="paper",
                       x=0.5, y=-0.14, showarrow=False,
                       font=dict(size=10, color="#6B7280"), align="center")

    fig.update_layout(title=f"📊 Distribution — <b>{col}</b>",
                      xaxis_title=col, yaxis_title="Frequency", showlegend=False)
    return _style(fig)


def _categorical_chart(df: pd.DataFrame, col: str) -> go.Figure:
    """Donut (≤5 cats), vertical bar (6–8), or ranked horizontal bar (>8)."""
    vc = df[col].value_counts()
    n  = len(vc)

    if n <= 5:
        fig = go.Figure(go.Pie(
            labels=vc.index.astype(str), values=vc.values, hole=0.45,
            marker=dict(colors=QUAL[:n], line=dict(color="white", width=3)),
            textinfo="label+percent+value",
            hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>%{percent}<extra></extra>"
        ))
        fig.update_layout(title=f"🥧 Breakdown — <b>{col}</b>",
                          legend=dict(orientation="h", y=-0.15))
        return _style(fig, height=420)

    if n <= 10:
        fig = go.Figure(go.Bar(
            x=vc.index.astype(str), y=vc.values,
            marker=dict(color=QUAL * 3, line=dict(width=0)),
            text=vc.values, textposition="outside",
            hovertemplate="<b>%{x}</b><br>Count: %{y:,}<extra></extra>"
        ))
        fig.update_layout(title=f"📋 Distribution — <b>{col}</b>",
                          xaxis_title=col, yaxis_title="Count",
                          xaxis_tickangle=-35)
        return _style(fig)

    # High cardinality → horizontal ranked bar
    top = vc.head(15).sort_values()
    fig = go.Figure(go.Bar(
        x=top.values, y=top.index.astype(str), orientation="h",
        marker=dict(color=top.values,
                    colorscale=[[0,"#E0E7FF"],[1,PALETTE["primary"]]],
                    showscale=False, line=dict(width=0)),
        text=[f"{v:,}" for v in top.values], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Count: %{x:,}<extra></extra>"
    ))
    fig.update_layout(title=f"🏷️ Top 15 — <b>{col}</b> ({n} unique values)",
                      xaxis_title="Count", yaxis=dict(automargin=True))
    h = max(380, min(15, n) * 34 + 120)
    return _style(fig, height=h)


def _correlation_heatmap(df: pd.DataFrame, cols: List[str]) -> go.Figure:
    """Annotated lower-triangle correlation heatmap."""
    cols = cols[:12]
    corr = df[cols].corr()
    z    = corr.values.copy().astype(float)
    # blank upper triangle
    for i in range(len(z)):
        for j in range(i+1, len(z)):
            z[i][j] = np.nan

    text_vals = np.where(np.isnan(z), "",
                         np.vectorize(lambda v: f"{v:.2f}")(z))

    fig = go.Figure(go.Heatmap(
        z=z, x=cols, y=cols, text=text_vals,
        texttemplate="%{text}", textfont_size=11,
        colorscale=DIV, zmid=0, zmin=-1, zmax=1,
        colorbar=dict(title="r", tickvals=[-1,-0.5,0,0.5,1]),
        hoverongaps=False,
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>r = %{z:.3f}<extra></extra>"
    ))
    h = max(480, len(cols)*54 + 80)
    fig.update_layout(title="🔗 Correlation Matrix (lower triangle)",
                      xaxis_tickangle=-35, yaxis=dict(automargin=True), height=h)
    return _style(fig, height=h)


def _scatter_trend(df: pd.DataFrame, x: str, y: str, color: str = None) -> go.Figure:
    """Scatter with OLS trendline and correlation annotation."""
    sub = df[[x, y] + ([color] if color else [])].dropna()
    r   = sub[x].corr(sub[y])
    strength = "strong" if abs(r) > 0.7 else "moderate" if abs(r) > 0.4 else "weak"
    direction = "positive ↑" if r > 0 else "negative ↓"

    kwargs = dict(trendline="ols", opacity=0.65,
                  color_discrete_sequence=QUAL)
    if color and color in df.select_dtypes(include=["object","category"]).columns.tolist():
        if df[color].nunique() <= 12:
            kwargs["color"] = color

    fig = px.scatter(sub, x=x, y=y, **kwargs)
    fig.update_layout(
        title=f"🔗 <b>{x}</b> vs <b>{y}</b>  —  r = {r:.3f}  ({strength} {direction})",
        xaxis_title=x, yaxis_title=y
    )
    return _style(fig)


def _box_by_category(df: pd.DataFrame, cat: str, num: str) -> go.Figure:
    """Box/violin depending on sample size."""
    n_cat = df[cat].nunique()
    use_violin = (len(df) > 200 and n_cat <= 10)

    if use_violin:
        fig = px.violin(df, x=cat, y=num, box=True, points="outliers",
                        color=cat, color_discrete_sequence=QUAL)
        kind = "Violin"
    else:
        fig = px.box(df, x=cat, y=num, color=cat, points="outliers",
                     color_discrete_sequence=QUAL, notched=False)
        kind = "Box"

    fig.update_layout(
        title=f"📦 {kind} — <b>{num}</b> by <b>{cat}</b>",
        xaxis_title=cat, yaxis_title=num, showlegend=False,
        xaxis_tickangle=-30 if n_cat > 5 else 0
    )
    return _style(fig)


def _grouped_bar_mean(df: pd.DataFrame, cat: str, num: str) -> go.Figure:
    """Mean bar chart when box isn't appropriate (many categories)."""
    agg = df.groupby(cat)[num].agg(["mean","sem"]).reset_index()
    agg = agg.sort_values("mean", ascending=False).head(20)

    fig = go.Figure(go.Bar(
        x=agg[cat].astype(str), y=agg["mean"],
        error_y=dict(type="data", array=agg["sem"].tolist(), visible=True),
        marker=dict(color=agg["mean"],
                    colorscale=[[0,"#E0E7FF"],[1,PALETTE["primary"]]],
                    showscale=False, line=dict(width=0)),
        text=agg["mean"].round(2), textposition="outside",
        hovertemplate="<b>%{x}</b><br>Mean: %{y:.2f}<br>SE: %{error_y.array:.2f}<extra></extra>"
    ))
    fig.update_layout(title=f"📊 Mean <b>{num}</b> by <b>{cat}</b>  (±SE)",
                      xaxis_title=cat, yaxis_title=f"Mean {num}",
                      xaxis_tickangle=-35)
    return _style(fig)


def _missing_map(df: pd.DataFrame) -> go.Figure:
    """Completeness bar, colour-coded green/amber/red."""
    miss = df.isnull().mean().sort_values(ascending=True) * 100
    comp = 100 - miss
    colors = [PALETTE["success"] if v >= 95 else PALETTE["warning"] if v >= 80 else PALETTE["danger"]
              for v in comp]

    fig = go.Figure(go.Bar(
        x=comp.values, y=comp.index, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in comp.values],
        textposition="inside", insidetextanchor="middle",
        hovertemplate="<b>%{y}</b><br>Complete: %{x:.1f}%<extra></extra>"
    ))
    fig.add_vline(x=95, line=dict(color="#10B981", width=1.5, dash="dot"),
                  annotation=dict(text="95%", font_size=10, font_color="#10B981"))
    h = max(280, len(df.columns)*26 + 80)
    fig.update_layout(title="🔍 Data Completeness per Column",
                      xaxis=dict(title="% Complete", range=[0, 108]),
                      yaxis=dict(automargin=True), height=h)
    return _style(fig, height=h)


def _outlier_overview(df: pd.DataFrame, num_cols: List[str]) -> go.Figure:
    """Z-score normalised multi-box — highlights outliers across all columns."""
    cols = num_cols[:8]
    norm = df[cols].apply(lambda s: (s - s.mean()) / (s.std() + 1e-9))

    fig = go.Figure()
    for idx, col in enumerate(cols):
        fig.add_trace(go.Box(
            y=norm[col], name=col, boxmean="sd",
            marker=dict(color=QUAL[idx % len(QUAL)], size=4, opacity=0.6),
            line_color=QUAL[idx % len(QUAL)],
            hovertemplate=f"<b>{col}</b><br>z = %{{y:.2f}}<extra></extra>"
        ))

    fig.update_layout(
        title="📦 Outlier Overview — Z-score Normalised  "
              "<span style='font-size:12px;color:#6B7280'>(whiskers = 1.5×IQR)</span>",
        yaxis_title="z-score", showlegend=False
    )
    return _style(fig)


def _scatter_matrix(df: pd.DataFrame, num_cols: List[str], cat_cols: List[str]) -> go.Figure:
    cols  = num_cols[:5]
    color = cat_cols[0] if cat_cols and df[cat_cols[0]].nunique() <= 10 else None

    kwargs = dict(dimensions=cols, opacity=0.55, color_discrete_sequence=QUAL)
    if color:
        kwargs["color"] = color
    fig = px.scatter_matrix(df, **kwargs)
    fig.update_traces(diagonal_visible=False, marker=dict(size=3))
    fig.update_layout(title="🔭 Pairwise Scatter Matrix", height=700)
    return _style(fig, height=700)


def _time_series(df: pd.DataFrame, time_col: str, num_cols: List[str]) -> go.Figure:
    df2 = df.copy()
    df2[time_col] = pd.to_datetime(df2[time_col], infer_datetime_format=True, errors="coerce")
    df2 = df2.dropna(subset=[time_col]).sort_values(time_col)

    fig = go.Figure()
    for idx, col in enumerate(num_cols[:4]):
        fig.add_trace(go.Scatter(
            x=df2[time_col], y=df2[col], mode="lines", name=col,
            line=dict(color=QUAL[idx], width=2.5),
            hovertemplate=f"<b>{col}</b>: %{{y:.2f}}<br>%{{x}}<extra></extra>"
        ))
    fig.update_layout(
        title="📈 Time Series — Trends Over Time",
        xaxis=dict(
            title=time_col,
            rangeselector=dict(buttons=[
                dict(count=7,  label="7D",  step="day",   stepmode="backward"),
                dict(count=1,  label="1M",  step="month", stepmode="backward"),
                dict(count=3,  label="3M",  step="month", stepmode="backward"),
                dict(step="all", label="All"),
            ]),
            rangeslider=dict(visible=True, thickness=0.05)
        ),
        yaxis_title="Value",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.08)
    )
    return _style(fig, height=540)


def _top_pairs(df: pd.DataFrame, num_cols: List[str], n: int = 3) -> List[Tuple[str,str,float]]:
    if len(num_cols) < 2:
        return []
    corr = df[num_cols].corr()
    pairs, seen = [], set()
    for i, c1 in enumerate(corr.columns):
        for j, c2 in enumerate(corr.columns):
            if i >= j:
                continue
            key = (min(c1,c2), max(c1,c2))
            if key in seen:
                continue
            seen.add(key)
            r = corr.loc[c1, c2]
            if abs(r) > 0.25:
                pairs.append((c1, c2, float(r)))
    pairs.sort(key=lambda t: abs(t[2]), reverse=True)
    return pairs[:n]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CLASS  (public API is backward-compatible)
# ─────────────────────────────────────────────────────────────────────────────

class DashboardVisualizer:
    """
    Intelligent dashboard — generates the most informative chart for each
    data characteristic, labelled and ready for Streamlit display.

    create_overview_dashboard()  returns  List[Tuple[str, go.Figure]]
    """

    def __init__(self, df: pd.DataFrame):
        self.df   = df.copy()
        self.num  = df.select_dtypes(include="number").columns.tolist()
        self.cat  = df.select_dtypes(include=["object","category"]).columns.tolist()
        self.dt   = df.select_dtypes(include="datetime64").columns.tolist()

        # Detect date strings
        for col in df.select_dtypes(include="object").columns:
            if col in self.dt:
                continue
            try:
                sample = df[col].dropna().head(30)
                parsed = pd.to_datetime(sample, infer_datetime_format=True, errors="coerce")
                if parsed.notna().mean() > 0.8:
                    self.dt.append(col)
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────

    def create_summary_metrics(self) -> Dict[str, Any]:
        m = dict(
            total_rows=len(self.df),
            total_columns=len(self.df.columns),
            numeric_columns=len(self.num),
            categorical_columns=len(self.cat),
            missing_values=int(self.df.isnull().sum().sum()),
            missing_percentage=round(
                self.df.isnull().sum().sum() / max(1, self.df.shape[0]*self.df.shape[1]) * 100, 2
            ),
            memory_usage_mb=round(self.df.memory_usage(deep=True).sum() / 1024**2, 2)
        )
        if self.num:
            m["numeric_stats"] = {
                col: dict(
                    mean=round(self.df[col].mean(), 2),
                    median=round(self.df[col].median(), 2),
                    std=round(self.df[col].std(), 2),
                    min=round(self.df[col].min(), 2),
                    max=round(self.df[col].max(), 2),
                )
                for col in self.num[:8]
            }
        return m

    def create_overview_dashboard(self) -> List[Tuple[str, go.Figure]]:
        """
        Returns a list of (label, figure) tuples — every chart is smart and
        richly annotated.
        """
        charts: List[Tuple[str, go.Figure]] = []

        # ── 1. DATA QUALITY ──────────────────────────────────────────────
        try:
            charts.append(("🔍 Data Completeness", _missing_map(self.df)))
        except Exception as e:
            logger.error(f"Missing map: {e}")

        # ── 2. NUMERIC DISTRIBUTIONS ─────────────────────────────────────
        for col in self.num[:6]:
            try:
                charts.append((f"📊 {col} — Distribution", _histogram_stats(self.df, col)))
            except Exception as e:
                logger.error(f"Histogram {col}: {e}")

        # ── 3. CORRELATION HEATMAP ───────────────────────────────────────
        if len(self.num) >= 3:
            try:
                charts.append(("🔗 Correlation Heatmap", _correlation_heatmap(self.df, self.num)))
            except Exception as e:
                logger.error(f"Corr heatmap: {e}")

        # ── 4. STRONGEST RELATIONSHIPS ───────────────────────────────────
        for x, y, r in _top_pairs(self.df, self.num, n=3):
            try:
                color_col = self.cat[0] if self.cat and self.df[self.cat[0]].nunique() <= 10 else None
                label = f"↔️ {x} vs {y}  (r={r:.2f})"
                charts.append((label, _scatter_trend(self.df, x, y, color_col)))
            except Exception as e:
                logger.error(f"Scatter {x}/{y}: {e}")

        # ── 5. CATEGORICAL DISTRIBUTIONS ─────────────────────────────────
        for col in self.cat[:4]:
            try:
                charts.append((f"🏷️ {col} — Categories", _categorical_chart(self.df, col)))
            except Exception as e:
                logger.error(f"Cat chart {col}: {e}")

        # ── 6. NUMERIC × CATEGORY interactions ───────────────────────────
        if self.cat and self.num:
            cat = self.cat[0]
            n_unique = self.df[cat].nunique()
            for num_col in self.num[:2]:
                try:
                    if n_unique <= 12:
                        charts.append((f"📦 {num_col} by {cat}",
                                       _box_by_category(self.df, cat, num_col)))
                    elif n_unique <= 30:
                        charts.append((f"📊 Mean {num_col} by {cat}",
                                       _grouped_bar_mean(self.df, cat, num_col)))
                except Exception as e:
                    logger.error(f"Cat×num {cat}/{num_col}: {e}")

        # ── 7. TIME SERIES ────────────────────────────────────────────────
        if self.dt and self.num:
            try:
                charts.append(("📈 Time Series", _time_series(self.df, self.dt[0], self.num)))
            except Exception as e:
                logger.error(f"Time series: {e}")

        # ── 8. OUTLIER OVERVIEW ───────────────────────────────────────────
        if len(self.num) >= 2:
            try:
                charts.append(("📦 Outlier Overview", _outlier_overview(self.df, self.num)))
            except Exception as e:
                logger.error(f"Outlier box: {e}")

        # ── 9. SCATTER MATRIX ─────────────────────────────────────────────
        if len(self.num) >= 3:
            try:
                charts.append(("🔭 Scatter Matrix", _scatter_matrix(self.df, self.num, self.cat)))
            except Exception as e:
                logger.error(f"Scatter matrix: {e}")

        logger.info(f"Generated {len(charts)} intelligent charts")
        return charts

    def create_custom_chart(
        self,
        chart_type: str,
        x: Optional[str] = None,
        y: Optional[str] = None,
        color: Optional[str] = None,
        title: Optional[str] = None
    ) -> Optional[go.Figure]:
        """Backward-compatible custom chart builder."""
        try:
            kw = dict(title=title, color=color, color_discrete_sequence=QUAL)
            if chart_type == "bar":
                fig = px.bar(self.df, x=x, y=y, **kw)
            elif chart_type == "line":
                fig = px.line(self.df, x=x, y=y, **kw)
            elif chart_type == "scatter":
                fig = px.scatter(self.df, x=x, y=y, trendline="ols", **kw)
            elif chart_type == "pie":
                fig = px.pie(self.df, names=x, values=y, title=title,
                             color_discrete_sequence=QUAL)
                fig.update_traces(hole=0.4, textinfo="label+percent+value")
            elif chart_type == "histogram":
                fig = px.histogram(self.df, x=x, nbins=40, **kw)
            elif chart_type == "box":
                fig = px.box(self.df, x=x, y=y, points="outliers", **kw)
            else:
                logger.warning(f"Unsupported chart type: {chart_type}")
                return None
            return _style(fig)
        except Exception as e:
            logger.error(f"Custom chart error: {e}")
            return None