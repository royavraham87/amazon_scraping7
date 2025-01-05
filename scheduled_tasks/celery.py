from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproj.settings')

# Create the Celery app instance with the name of the project or app.
app = Celery('scheduled_tasks')

# Configure Celery to use Django settings with the `CELERY_` namespace.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks in all installed apps.
try:
    app.autodiscover_tasks()
    logging.info("Celery: Tasks discovered successfully in installed apps.")
except Exception as e:
    logging.error(f"Celery: Error discovering tasks: {str(e)}", exc_info=True)

@app.task(bind=True)
def debug_task(self):
    """
    Debugging task to verify Celery is working correctly.
    Logs the current request object for debugging.
    """
    logging.info(f'Celery Debug Task - Request: {self.request!r}')
    print(f'Celery Debug Task - Request: {self.request!r}')

# Additional Logging for App Initialization
try:
    logging.info("Celery: Application initialized successfully.")
except Exception as e:
    logging.error(f"Celery: Initialization error: {str(e)}", exc_info=True)
