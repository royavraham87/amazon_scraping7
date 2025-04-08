import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from scheduled_tasks.actions import run_scraping

scheduler = BackgroundScheduler()

async def async_scraping_wrapper():
    """Ensures the scraping task runs in an async-compatible way."""
    try:
        print("⏳ Running scheduled scraping...")
        await run_scraping()
        print("✅ Scheduled scraping completed successfully.")
    except Exception as e:
        print(f"❌ Error during scheduled scraping: {e}")

def start_scheduler():
    """Starts the scheduler and ensures the scraping task runs weekly."""
    try:
        scheduler.add_job(
            lambda: asyncio.run(async_scraping_wrapper()),  # Using a wrapper to handle async
            'interval',
            weeks=1  # Runs every week
        )
        scheduler.start()
        print("✅ Scheduler started successfully.")
    except Exception as e:
        print(f"❌ Error starting scheduler: {e}")

