from django.apps import AppConfig

class ClaimConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Claim'

    def ready(self):
        from . import scheduler
        scheduler.start()  # Start the scheduler when the app is ready