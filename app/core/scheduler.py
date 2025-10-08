from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from app.core.database import SessionLocal
from app.services.scheduler_service import SchedulerService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure scheduler
executors = {
    'default': ThreadPoolExecutor(20),
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)

def daily_lesson_unlock_job():
    """Scheduled job to unlock due lessons"""
    db = SessionLocal()
    try:
        service = SchedulerService(db)
        unlocked_count = service.unlock_due_lessons()
        logger.info(f"Daily lesson unlock job completed: Unlocked {unlocked_count} lessons")
        return unlocked_count
    except Exception as e:
        logger.error(f"Daily lesson unlock job failed: {e}")
        raise
    finally:
        db.close()

def daily_reminder_job():
    """Send daily reminders to users"""
    db = SessionLocal()
    try:
        service = SchedulerService(db)
        sent_count = service.send_daily_reminders()
        logger.info(f"Daily reminder job completed: Sent {sent_count} reminders")
        return sent_count
    except Exception as e:
        logger.error(f"Daily reminder job failed: {e}")
        raise
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    try:
        # Add lesson unlock job (runs every hour)
        scheduler.add_job(
            daily_lesson_unlock_job,
            trigger=CronTrigger(minute=0),  # Every hour at minute 0
            id='hourly_lesson_unlock',
            name='Hourly Lesson Unlock Job',
            replace_existing=True
        )
        
        # Add daily reminder job runs every hour
        scheduler.add_job(
            daily_reminder_job,
            trigger=CronTrigger(minute=0),
            id='daily_reminder',
            name='Daily Reminder Job',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Background scheduler started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise

def stop_scheduler():
    """Stop the background scheduler"""
    try:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

def get_scheduler_status():
    """Get current scheduler status"""
    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    }
