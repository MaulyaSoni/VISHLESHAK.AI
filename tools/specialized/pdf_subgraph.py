"""
Vishleshak v2 — PDF Report Subgraph
=====================================
Called by report_agent in supervisor_graph.py.

Two modes:
  "auto"   → 3-page summary PDF
  "manual" → Full 7-page boardroom report
"""

import os
import logging
from datetime import datetime
from typing import Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image as RLImage
)

logger = logging.getLogger("vishleshak.pdf_subgraph")

DOMAIN_COLORS = {
    "finance": {"primary": colors.HexColor("#1A3A5C"), "accent": colors.HexColor("#2E86AB"), "label": "Finance"},
    "insurance": {"primary": colors.HexColor("#1A4A2E"), "accent": colors.HexColor("#2EAB6E"), "label": "Insurance"},
    "general": {"primary": colors.HexColor("#2A1A4A"), "accent": colors.HexColor("#7B4EAB"), "label": "General"},
}

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

C_WHITE = colors.white
C_BLACK = colors.HexColor("#1A1A1A")
C_MUTED = colors.HexColor("#6B7280")
C_BORDER = colors.HexColor("#E5E7EB")
C_ROW_ODD = colors.HexColor("#F9FAFB")
C_ROW_EVEN = colors.white
C_GREEN = colors.HexColor("#10B981")
C_AMBER = colors.HexColor("#F59E0B")
C_RED = colors.HexColor("#EF4444")


def _build_styles(domain: str = "general") -> dict:
    dc = DOMAIN_COLORS.get(domain, DOMAIN_COLORS["general"])
    base = getSampleStyleSheet()

    return {
        "cover_title": ParagraphStyle("cover_title", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=28, textColor=C_WHITE, leading=34, spaceAfter=8),
        "section_heading": ParagraphStyle("section_heading", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=14, textColor=dc["primary"], leading=18, spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["Normal"], fontName="Helvetica", fontSize=10, textColor=C_BLACK, leading=15, spaceAfter=6),
        "body_muted": ParagraphStyle("body_muted", parent=base["Normal"], fontName="Helvetica", fontSize=9, textColor=C_MUTED, leading=14, spaceAfter=4),
        "bullet": ParagraphStyle("bullet", parent=base["Normal"], fontName="Helvetica", fontSize=10, textColor=C_BLACK, leading=15, leftIndent=12, spaceAfter=4),
        "flag": ParagraphStyle("flag", parent=base["Normal"], fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#92400E"), leading=15, leftIndent=12, spaceAfter=4),
        "table_header": ParagraphStyle("table_header", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=C_WHITE, leading=12),
        "table_cell": ParagraphStyle("table_cell", parent=base["Normal"], fontName="Helvetica", fontSize=9, textColor=C_BLACK, leading=12),
        "caption": ParagraphStyle("caption", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=8, textColor=C_MUTED, leading=11, alignment=TA_CENTER, spaceAfter=8),
        "footer": ParagraphStyle("footer", parent=base["Normal"], fontName="Helvetica", fontSize=7, textColor=C_MUTED, leading=10, alignment=TA_CENTER),
        "domain_color": dc,
    }


class _PageTemplate:
    def __init__(self, domain: str, dataset_name: str, total_pages_ref: list):
        self.dc = DOMAIN_COLORS.get(domain, DOMAIN_COLORS["general"])
        self.dataset_name = dataset_name
        self.total_pages = total_pages_ref
        self.generated = datetime.now().strftime("%d %b %Y, %H:%M")

    def on_page(self, canvas, doc):
        canvas.saveState()
        page_num = doc.page

        canvas.setFillColor(self.dc["accent"])
        canvas.rect(0, PAGE_H - 3 * mm, PAGE_W, 3 * mm, fill=1, stroke=0)

        canvas.setStrokeColor(C_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(MARGIN, 9 * mm, f"Vishleshak AI  ·  {self.dataset_name}  ·  Confidential")
        canvas.drawRightString(PAGE_W - MARGIN, 9 * mm, f"Generated {self.generated}  ·  Page {page_num}")

        canvas.restoreState()

    def on_first_page(self, canvas, doc):
        pass


def _section_divider(dc: dict) -> list:
    return [HRFlowable(width="100%", thickness=1.5, color=dc["accent"], spaceAfter=8, spaceBefore=4)]


def _kv_table(rows: list, styles_dict: dict, dc: dict) -> Table:
    data = [[Paragraph(f"<b>{k}</b>", styles_dict["table_cell"]), Paragraph(str(v), styles_dict["table_cell"])] for k, v in rows]
    col_widths = [CONTENT_W * 0.45, CONTENT_W * 0.55]
    t = Table(data, colWidths=col_widths, repeatRows=0)
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_ROW_ODD, C_ROW_EVEN]),
        ("GRID", (0, 0), (-1, -1), 0.3, C_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _health_bar(score: float, styles_dict: dict) -> Table:
    color = C_GREEN if score >= 70 else C_AMBER if score >= 40 else C_RED
    label = "Good" if score >= 70 else "Fair" if score >= 40 else "Poor"

    data = [[Paragraph(f"<b>Data Health Score</b>", styles_dict["table_cell"]), Paragraph(f"<b>{score:.0f}/100</b> - {label}", styles_dict["table_cell"])]]
    t = Table(data, colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F3F4F6")),
        ("BACKGROUND", (1, 0), (1, 0), color),
        ("TEXTCOLOR", (1, 0), (1, 0), C_WHITE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.3, C_BORDER),
    ]))
    return t


def _stats_table(meta: dict, styles_dict: dict, dc: dict) -> Table:
    profile = meta.get("profile", {})
    numeric_cols = profile.get("numeric_columns", [])[:8]

    if not numeric_cols:
        return Paragraph("No numeric columns found.", styles_dict["body_muted"])

    stats = meta.get("statistics", {})

    headers = ["Column", "Mean", "Median", "Std Dev", "Min", "Max"]
    data = [[Paragraph(f"<b>{h}</b>", styles_dict["table_header"]) for h in headers]]

    for col in numeric_cols:
        col_stats = stats.get(col, {})
        row = [
            Paragraph(col[:22], styles_dict["table_cell"]),
            Paragraph(f"{col_stats.get('mean', 'N/A'):.2f}" if isinstance(col_stats.get('mean'), (int, float)) else "N/A", styles_dict["table_cell"]),
            Paragraph(f"{col_stats.get('median', 'N/A'):.2f}" if isinstance(col_stats.get('median'), (int, float)) else "N/A", styles_dict["table_cell"]),
            Paragraph(f"{col_stats.get('std', 'N/A'):.2f}" if isinstance(col_stats.get('std'), (int, float)) else "N/A", styles_dict["table_cell"]),
            Paragraph(f"{col_stats.get('min', 'N/A'):.2f}" if isinstance(col_stats.get('min'), (int, float)) else "N/A", styles_dict["table_cell"]),
            Paragraph(f"{col_stats.get('max', 'N/A'):.2f}" if isinstance(col_stats.get('max'), (int, float)) else "N/A", styles_dict["table_cell"]),
        ]
        data.append(row)

    col_widths = [CONTENT_W * 0.22] + [CONTENT_W * 0.13] * 5
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), dc["primary"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_ROW_ODD, C_ROW_EVEN]),
        ("GRID", (0, 0), (-1, -1), 0.3, C_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))
    return t


def _embed_chart(chart_path: str, caption: str, styles_dict: dict, max_width: float = None) -> list:
    if not chart_path or not os.path.exists(chart_path):
        return [Paragraph(f"[Chart unavailable: {os.path.basename(chart_path or '')}]", styles_dict["body_muted"])]
    w = max_width or CONTENT_W
    try:
        img = RLImage(chart_path, width=w, height=w * 0.5)
        return [img, Paragraph(caption, styles_dict["caption"]), Spacer(1, 6)]
    except Exception as e:
        return [Paragraph(f"[Chart load error: {e}]", styles_dict["body_muted"])]


def _node_cover_page(state: dict, styles: dict, dc: dict) -> list:
    story = []
    domain = state.get("domain", "general")
    name = state.get("dataset_name", "Dataset")
    meta = state.get("dataset_meta", {})
    shape = meta.get("shape", {})
    mode = state.get("pdf_trigger", "auto")
    now = datetime.now().strftime("%d %B %Y")

    cover_bg = Table([[Paragraph("", styles["body"])]], colWidths=[PAGE_W - 2 * MARGIN], rowHeights=[60 * mm])
    cover_bg.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), dc["primary"]),
        ("TOPPADDING", (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
    ]))
    story.append(cover_bg)
    story.append(Spacer(1, 8))

    story.append(Paragraph(f'<font color="{dc["accent"].hexval()}" size="10"><b>{dc["label"].upper()} INTELLIGENCE REPORT</b></font>', styles["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(name, ParagraphStyle("ct", fontName="Helvetica-Bold", fontSize=24, textColor=dc["primary"], leading=30, spaceAfter=6)))
    story.append(Paragraph(f"Autonomous analysis by Vishleshak AI  -  {now}", styles["body_muted"]))
    story.append(Spacer(1, 12))

    rows = [
        ("Rows", f"{shape.get('rows', 0):,}"),
        ("Columns", f"{shape.get('cols', 0)}"),
        ("Report type", "Executive Summary" if mode == "auto" else "Full Analysis"),
        ("Domain", dc["label"]),
    ]
    story.append(_kv_table(rows, styles, dc))
    story.append(PageBreak())
    return story


def _node_summary_page(state: dict, styles: dict, dc: dict) -> list:
    story = []
    insights_text = state.get("insights_text", "")
    meta = state.get("dataset_meta", {})

    story += [Paragraph("Executive Summary", styles["section_heading"])]
    story += _section_divider(dc)

    summary = insights_text[:600] if insights_text else "No summary available."
    story.append(Paragraph(summary, styles["body"]))
    story.append(Spacer(1, 10))

    profile = meta.get("profile", {})
    if profile:
        health = 100 - min(profile.get("missing_pct", 0), 100)
        if health:
            story.append(_health_bar(float(health), styles))
            story.append(Spacer(1, 10))

    flags = state.get("proactive_flags", [])
    if flags:
        story.append(Paragraph("Key Findings", styles["section_heading"]))
        story += _section_divider(dc)
        for f in flags[:5]:
            story.append(Paragraph(str(f), styles["bullet"]))
        story.append(Spacer(1, 8))

    return story


def _node_stats_page(state: dict, styles: dict, dc: dict) -> list:
    story = []
    meta = state.get("dataset_meta", {})

    story += [Paragraph("Statistical Profile", styles["section_heading"])]
    story += _section_divider(dc)

    story.append(_stats_table(meta, styles, dc))
    story.append(Spacer(1, 12))

    return story


def _node_charts_page(state: dict, styles: dict, dc: dict) -> list:
    story = []
    charts = state.get("charts", [])

    if not charts:
        return []

    story += [Paragraph("Visual Analysis", styles["section_heading"])]
    story += _section_divider(dc)

    chart_labels = ["Distribution analysis", "Correlation view", "Category distribution", "Variable relationship"]

    for i, chart_path in enumerate(charts[:4]):
        caption = chart_labels[i] if i < len(chart_labels) else f"Chart {i+1}"
        story += _embed_chart(chart_path, caption, styles)
        if i < len(charts) - 1:
            story.append(Spacer(1, 6))

    return story


def _node_findings_page(state: dict, styles: dict, dc: dict) -> list:
    story = []
    flags = state.get("proactive_flags", [])

    if flags:
        story += [Paragraph("Anomalies & Alerts", styles["section_heading"])]
        story += _section_divider(dc)
        for f in flags[:6]:
            story.append(Paragraph(str(f), styles["flag"]))
        story.append(Spacer(1, 8))

    return story


def _node_domain_page(state: dict, styles: dict, dc: dict) -> list:
    domain = state.get("domain", "general")
    story = []

    if domain == "finance":
        story += [Paragraph("Financial Intelligence", styles["section_heading"])]
        story += _section_divider(dc)
        story.append(Paragraph(
            "Financial pattern detection applied to the dataset. "
            "These findings should be reviewed by a qualified financial analyst.",
            styles["body_muted"]
        ))
        story.append(Spacer(1, 8))
        story.append(Paragraph("- Review revenue and expense trends for seasonality", styles["bullet"]))
        story.append(Paragraph("- Check for unusual correlations between metrics", styles["bullet"]))
        story.append(Paragraph("- Validate significant outliers against source data", styles["bullet"]))

    elif domain == "insurance":
        story += [Paragraph("Insurance Intelligence", styles["section_heading"])]
        story += _section_divider(dc)
        story.append(Paragraph(
            "Insurance-specific pattern analysis applied. "
            "Findings should be validated against IRDAI guidelines.",
            styles["body_muted"]
        ))
        story.append(Spacer(1, 8))
        story.append(Paragraph("- Monitor loss ratio trends across periods", styles["bullet"]))
        story.append(Paragraph("- Review claim frequency distributions", styles["bullet"]))
        story.append(Paragraph("- Check for premium adequacy signals", styles["bullet"]))

    elif domain == "ecommerce":
        story += [Paragraph("E-Commerce Intelligence", styles["section_heading"])]
        story += _section_divider(dc)
        story.append(Paragraph(
            "E-commerce specific pattern analysis applied.",
            styles["body_muted"]
        ))
        story.append(Spacer(1, 8))
        story.append(Paragraph("- Analyze customer churn indicators", styles["bullet"]))
        story.append(Paragraph("- Review basket size trends", styles["bullet"]))
        story.append(Paragraph("- Check return rate patterns", styles["bullet"]))

    return story


def generate_pdf_report(state: dict, mode: str = "auto") -> Optional[str]:
    """Generate PDF report from supervisor state."""
    user_id = state.get("user_id", "default")
    domain = state.get("domain", "general")
    name = state.get("dataset_name", "dataset") or "dataset"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_tag = "summary" if mode == "auto" else "full_report"

    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)[:40]
    out_dir = os.path.join("storage", "exports", user_id)
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, f"vishleshak_{mode_tag}_{safe_name}_{ts}.pdf")

    styles = _build_styles(domain)
    dc = styles["domain_color"]

    page_tmpl = _PageTemplate(domain, name, [])

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=20 * mm,
        title=f"Vishleshak AI - {name}",
        author="Vishleshak AI",
        subject=f"{dc['label']} Analysis Report",
    )

    story = []

    story += _node_cover_page(state, styles, dc)
    story += _node_summary_page(state, styles, dc)

    if mode == "auto":
        charts = state.get("charts", [])
        if charts:
            story.append(PageBreak())
            story += _node_charts_page(state, styles, dc)
    else:
        story.append(PageBreak())
        story += _node_stats_page(state, styles, dc)

        charts = state.get("charts", [])
        if charts:
            story.append(PageBreak())
            story += _node_charts_page(state, styles, dc)

        anomaly_story = _node_findings_page(state, styles, dc)
        if anomaly_story:
            story.append(PageBreak())
            story += anomaly_story

        domain_story = _node_domain_page(state, styles, dc)
        if domain_story:
            story.append(PageBreak())
            story += domain_story

    doc.build(
        story,
        onFirstPage=page_tmpl.on_first_page,
        onLaterPages=page_tmpl.on_page,
    )

    logger.info(f"PDF [{mode}] generated: {pdf_path}")
    return pdf_path