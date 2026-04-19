"""
Analysis Repository — CRUD for Data Agent analysis reports
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .db_manager import get_db
from .models import AnalysisReport

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AnalysisRepository:
    """All analysis report database operations."""

    def create_report(
        self,
        user_id: int,
        session_id: str,
        title: str,
        instruction: str,
        dataset_name: Optional[str] = None,
        dataset_rows: Optional[int] = None,
        dataset_cols: Optional[int] = None,
        mode: str = "Analysis Only",
        report_data: Optional[Dict[str, Any]] = None,
        status: str = "running",
    ) -> AnalysisReport:
        """Create a new analysis report entry."""
        with get_db() as db:
            report = AnalysisReport(
                user_id=user_id,
                session_id=session_id,
                title=title[:300],
                instruction=instruction[:1000],
                dataset_name=dataset_name[:200] if dataset_name else None,
                dataset_rows=dataset_rows,
                dataset_cols=dataset_cols,
                mode=mode,
                status=status,
                full_report=json.dumps(report_data) if report_data else None,
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            logger.info("📊 Analysis report %s created for user %s", report.id, user_id)
            return report

    def update_report(
        self,
        report_id: int,
        report_data: Dict[str, Any],
        status: str = "completed",
        error_message: Optional[str] = None,
    ) -> Optional[AnalysisReport]:
        """Update report with complete analysis results."""
        with get_db() as db:
            report = db.get(AnalysisReport, report_id)
            if not report:
                return None
            
            # Extract key fields from report data
            insights = report_data.get("insights", {})
            metadata = report_data.get("metadata", {})
            ml_results = report_data.get("ml_results", {})
            charts = report_data.get("charts", [])
            
            report.executive_summary = insights.get("executive_summary", "")[:2000]
            report.key_findings = json.dumps(insights.get("key_findings", []))
            report.recommendations = json.dumps(insights.get("recommendations", []))
            report.anomalies = json.dumps(insights.get("anomalies_or_risks", []))
            report.charts_info = json.dumps([{
                "title": c.get("title", ""),
                "type": c.get("type", ""),
                "html_path": c.get("html_path", ""),
                "png_path": c.get("png_path", ""),
            } for c in charts])
            report.ml_metrics = json.dumps(ml_results.get("metrics", {}))
            report.notebook_path = report_data.get("notebook_path", "")
            report.full_report = json.dumps(report_data)
            report.status = status
            report.error_message = error_message
            report.updated_at = _utcnow()
            
            db.commit()
            logger.info("📊 Analysis report %s updated with status: %s", report_id, status)
            return report

    def get_report(self, report_id: int) -> Optional[AnalysisReport]:
        """Get a single report by ID."""
        with get_db() as db:
            return db.get(AnalysisReport, report_id)

    def get_report_by_session(self, session_id: str) -> Optional[AnalysisReport]:
        """Get report by session ID."""
        with get_db() as db:
            return (
                db.query(AnalysisReport)
                .filter(AnalysisReport.session_id == session_id)
                .order_by(AnalysisReport.created_at.desc())
                .first()
            )

    def get_user_reports(
        self,
        user_id: int,
        limit: int = 50,
        include_completed_only: bool = False,
    ) -> List[AnalysisReport]:
        """Get all analysis reports for a user."""
        with get_db() as db:
            q = db.query(AnalysisReport).filter(AnalysisReport.user_id == user_id)
            if include_completed_only:
                q = q.filter(AnalysisReport.status == "completed")
            return (
                q.order_by(AnalysisReport.created_at.desc())
                .limit(limit)
                .all()
            )

    def delete_report(self, report_id: int) -> bool:
        """Delete a report."""
        with get_db() as db:
            report = db.get(AnalysisReport, report_id)
            if report:
                db.delete(report)
                db.commit()
                logger.info("📊 Analysis report %s deleted", report_id)
                return True
            return False

    def get_full_report_data(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Get the complete report data as dictionary."""
        with get_db() as db:
            report = db.get(AnalysisReport, report_id)
            if report and report.full_report:
                try:
                    return json.loads(report.full_report)
                except json.JSONDecodeError:
                    return None
            return None


# Global instance
analysis_repository = AnalysisRepository()
