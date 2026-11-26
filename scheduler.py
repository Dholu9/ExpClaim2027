from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

def send_daily_email():
    try:
        # Trigger the management command
        call_command('send_daily_email')
        logger.info("Daily email sent successfully.")
    except Exception as e:
        logger.error("Error sending daily email: %s", e)

def start():
    scheduler = BackgroundScheduler()
    # Schedule to run at 07:00 AM for testing
    scheduler.add_job(send_daily_email, trigger=CronTrigger(hour=7, minute=0))
    scheduler.start()