# scheduled_tasks/apps.py

from django.apps import AppConfig
import atexit
from scheduled_tasks.scheduler import start_scheduler, scheduler
from apscheduler.triggers.interval import IntervalTrigger
from scheduled_tasks.tasks import scheduled_scraping

class ScheduledTasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduled_tasks'

    def ready(self):
        """Starts the scheduler and registers scraping jobs when the app is ready."""
        if scheduler.state != 1:
            print("✅ Starting APScheduler from ScheduledTasksConfig...")
            start_scheduler()

            scheduler.add_job(
                scheduled_scraping,
                trigger=IntervalTrigger(days=1),
                id='daily_scraping_job',
                name='Daily scraping job',
                replace_existing=True
            )

            atexit.register(lambda: scheduler.shutdown(wait=False))
