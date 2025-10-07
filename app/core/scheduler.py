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

def daily_streak_update_job():
    """Update user streaks daily"""
    db = SessionLocal()
    try:
        service = SchedulerService(db)
        updated_count = service.update_user_streaks()
        logger.info(f"Daily streak update job completed: Updated {updated_count} users")
        return updated_count
    except Exception as e:
        logger.error(f"Daily streak update job failed: {e}")
        raise
    finally:
        db.close()

def daily_category_completion_check_job():
    """Check category completions daily"""
    db = SessionLocal()
    try:
        service = SchedulerService(db)
        updated_count = service.check_category_completions()
        logger.info(f"Daily category completion check job completed: Updated {updated_count} journeys")
        return updated_count
    except Exception as e:
        logger.error(f"Daily category completion check job failed: {e}")
        raise
    finally:
        db.close()

def weekly_progress_cleanup_job():
    """Weekly job to clean up old data and update statistics"""
    db = SessionLocal()
    try:
        service = SchedulerService(db)
        cleanup_stats = service.cleanup_old_data()
        logger.info(f"Weekly cleanup job completed: {cleanup_stats}")
        return cleanup_stats
    except Exception as e:
        logger.error(f"Weekly cleanup job failed: {e}")
    finally:
        db.close()

def daily_report_generation_job():
    """Generate daily reports"""
    db = SessionLocal()
    try:
        service = SchedulerService(db)
        report = service.generate_daily_reports()
        logger.info(f"Daily report generation job completed: {report}")
        return report
    except Exception as e:
        logger.error(f"Daily report generation job failed: {e}")
        raise
    finally:
        db.close()

def daily_backup_job():
    """Create daily backup of user data"""
    db = SessionLocal()
    try:
        service = SchedulerService(db)
        backup_info = service.backup_user_data()
        logger.info(f"Daily backup job completed: {backup_info}")
        return backup_info
    except Exception as e:
        logger.error(f"Daily backup job failed: {e}")
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
        
        # Add daily reminder job (runs at 9 AM)
        scheduler.add_job(
            daily_reminder_job,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_reminder',
            name='Daily Reminder Job',
            replace_existing=True
        )
        
        # Add daily streak update job (runs at 1 AM)
        scheduler.add_job(
            daily_streak_update_job,
            trigger=CronTrigger(hour=1, minute=0),
            id='daily_streak_update',
            name='Daily Streak Update Job',
            replace_existing=True
        )
        
        # Add daily category completion check job (runs at 2 AM)
        scheduler.add_job(
            daily_category_completion_check_job,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_category_completion_check',
            name='Daily Category Completion Check Job',
            replace_existing=True
        )
        
        # Add daily report generation job (runs at 3 AM)
        scheduler.add_job(
            daily_report_generation_job,
            trigger=CronTrigger(hour=3, minute=0),
            id='daily_report_generation',
            name='Daily Report Generation Job',
            replace_existing=True
        )
        
        # Add daily backup job (runs at 4 AM)
        scheduler.add_job(
            daily_backup_job,
            trigger=CronTrigger(hour=4, minute=0),
            id='daily_backup',
            name='Daily Backup Job',
            replace_existing=True
        )
        
        # Add weekly cleanup job (runs every Sunday at 1 AM)
        scheduler.add_job(
            weekly_progress_cleanup_job,
            trigger=CronTrigger(day_of_week=6, hour=1, minute=0),  # Sunday 1 AM
            id='weekly_cleanup',
            name='Weekly Progress Cleanup Job',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Background scheduler started successfully with all jobs")
        
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
