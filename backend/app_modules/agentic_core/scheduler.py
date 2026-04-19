"""
Scheduler / Automation Layer
Natural Language pipeline configuration with APScheduler
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler not available, scheduling disabled")


class PipelineConfig:
    """Configuration for automated pipelines"""
    
    VALID_SCHEDULES = [
        "hourly", "daily", "weekly", "monthly",
        "every_monday_09:00", "every_tuesday_09:00",
        "every_wednesday_09:00", "every_thursday_09:00",
        "every_friday_09:00"
    ]
    
    VALID_PIPELINES = [
        "data_agent", "insight_agent", "viz_agent", 
        "report_agent", "full_analysis"
    ]
    
    VALID_OUTPUTS = ["auto_pdf", "email_summary", "dashboard_alert"]
    
    @classmethod
    def from_nl(cls, nl_description: str) -> Dict[str, Any]:
        """
        Parse natural language description into config
        
        Example: "Every Monday, analyse my sales file and flag anomalies"
        """
        nl_lower = nl_description.lower()
        
        schedule = "weekly"
        if "every monday" in nl_lower:
            schedule = "every_monday_09:00"
        elif "every tuesday" in nl_lower:
            schedule = "every_tuesday_09:00"
        elif "daily" in nl_lower:
            schedule = "daily"
        elif "hourly" in nl_lower:
            schedule = "hourly"
        elif "monthly" in nl_lower:
            schedule = "monthly"
        
        pipeline = ["data_agent", "insight_agent", "report_agent"]
        if "chart" in nl_lower or "visual" in nl_lower:
            pipeline.append("viz_agent")
        
        output = ["auto_pdf"]
        if "email" in nl_lower:
            output.append("email_summary")
        if "alert" in nl_lower:
            output.append("dashboard_alert")
        
        return {
            "schedule": schedule,
            "source": "last_uploaded",
            "pipeline": pipeline,
            "output": output,
            "created_at": datetime.now().isoformat(),
            "description": nl_description
        }
    
    @classmethod
    def validate(cls, config: Dict[str, Any]) -> tuple:
        """Validate config, return (is_valid, error_message)"""
        if config.get("schedule") not in cls.VALID_SCHEDULES:
            return False, f"Invalid schedule: {config.get('schedule')}"
        
        for pipe in config.get("pipeline", []):
            if pipe not in cls.VALID_PIPELINES:
                return False, f"Invalid pipeline: {pipe}"
        
        for out in config.get("output", []):
            if out not in cls.VALID_OUTPUTS:
                return False, f"Invalid output: {out}"
        
        return True, None


class JobExecutor(ABC):
    """Abstract base for job executors"""
    
    @abstractmethod
    def execute(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the job and return result"""
        pass


class AnalysisJobExecutor(JobExecutor):
    """Executes analysis jobs via supervisor graph"""
    
    def execute(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"🔄 Executing scheduled job: {job_config.get('description')}")
        
        try:
            from agentic_core.supervisor_graph import invoke_supervisor
            
            pipeline = job_config.get("pipeline", ["data_agent", "insight_agent"])
            source = job_config.get("source", "last_uploaded")
            
            dataset = None
            if source == "last_uploaded":
                from utils.data_loader import DataLoader
                upload_folder = "data/uploads"
                files = sorted(
                    [f for f in os.listdir(upload_folder) if f.endswith((".csv", ".xlsx"))],
                    key=os.path.getmtime,
                    reverse=True
                )
                if files:
                    dataset = DataLoader.load_file(os.path.join(upload_folder, files[0]))[0]
            
            if dataset is None:
                return {"success": False, "error": "No dataset available"}
            
            result = invoke_supervisor(
                user_query="Scheduled analysis",
                dataset=dataset,
                user_id=job_config.get("user_id", "default"),
                domain=job_config.get("domain", "general")
            )
            
            pdf_path = result.get("pdf_path")
            
            return {
                "success": True,
                "pdf_path": pdf_path,
                "insights": result.get("insights_text", "")[:200],
                "charts_count": len(result.get("charts", []))
            }
        
        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            return {"success": False, "error": str(e)}


class SchedulerManager:
    """
    Manages scheduled jobs for Vishleshak AI
    """
    
    def __init__(self):
        self.scheduler = None
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.executor = AnalysisJobExecutor()
        
        if APSCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
            logger.info("✅ Scheduler initialized")
        else:
            logger.warning("Scheduler not available")
    
    def parse_schedule(self, schedule_str: str) -> tuple:
        """Parse schedule string to trigger"""
        if not APSCHEDULER_AVAILABLE:
            return None, "Scheduler not available"
        
        if schedule_str == "hourly":
            return IntervalTrigger(hours=1), "hourly"
        
        elif schedule_str == "daily":
            return CronTrigger(hour=9, minute=0), "daily at 9am"
        
        elif schedule_str == "weekly":
            return CronTrigger(day_of_week="monday", hour=9, minute=0), "weekly on Monday"
        
        elif schedule_str == "monthly":
            return CronTrigger(day=1, hour=9, minute=0), "monthly on 1st"
        
        elif schedule_str.startswith("every_"):
            parts = schedule_str.replace("every_", "").split("_")
            days = {"monday": 0, "tuesday": 1, "wednesday": 2, 
                   "thursday": 3, "friday": 4}
            if parts[0] in days and len(parts) > 1:
                time_parts = parts[1].split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                return CronTrigger(day_of_week=days[parts[0]], hour=hour, minute=minute), schedule_str
        
        return CronTrigger(hour=9, minute=0), "daily at 9am"
    
    def create_job(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create and schedule a new job"""
        is_valid, error = PipelineConfig.validate(job_config)
        if not is_valid:
            return {"success": False, "error": error}
        
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job_config["job_id"] = job_id
        
        trigger, schedule_desc = self.parse_schedule(job_config.get("schedule", "daily"))
        
        if self.scheduler:
            self.scheduler.add_job(
                func=self._execute_job,
                trigger=trigger,
                args=[job_config],
                id=job_id,
                replace_existing=True
            )
        
        self.jobs[job_id] = job_config
        
        logger.info(f"✅ Created job: {job_id} ({schedule_desc})")
        
        return {
            "success": True,
            "job_id": job_id,
            "schedule": schedule_desc
        }
    
    def _execute_job(self, job_config: Dict[str, Any]):
        """Internal job executor"""
        try:
            result = self.executor.execute(job_config)
            
            if job_config.get("output") and "auto_pdf" in job_config["output"]:
                if result.get("pdf_path"):
                    logger.info(f"📄 PDF saved: {result['pdf_path']}")
            
            if job_config.get("output") and "email_summary" in job_config["output"]:
                logger.info("📧 Would send email summary (SMTP not configured)")
            
            logger.info(f"✅ Job {job_config.get('job_id')} completed")
            return result
        
        except Exception as e:
            logger.error(f"Job execution error: {e}")
            return {"success": False, "error": str(e)}
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs"""
        return [
            {
                "job_id": job_id,
                "description": config.get("description", ""),
                "schedule": config.get("schedule", ""),
                "pipeline": config.get("pipeline", []),
                "created_at": config.get("created_at", "")
            }
            for job_id, config in self.jobs.items()
        ]
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a scheduled job"""
        if job_id in self.jobs:
            if self.scheduler:
                self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"✅ Deleted job: {job_id}")
            return True
        return False
    
    def shutdown(self):
        """Shutdown scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")


_scheduler_instance = None

def get_scheduler_manager() -> SchedulerManager:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerManager()
    return _scheduler_instance


def parse_nl_schedule(nl_text: str) -> Dict[str, Any]:
    """Parse natural language to schedule config"""
    return PipelineConfig.from_nl(nl_text)