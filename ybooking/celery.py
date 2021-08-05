import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ybooking.settings')

app = Celery('ybooking')
# app.conf.broker_url = 'redis://localhost:6379/0'
# app.conf.result_backend = 'redis://localhost:6379/0'
# app.conf.result_backend_transport_options = {
#     'retry_policy': {
#         'timeout': 5.0
#     }
# }
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'generate-timeslots': {
        'task': 'ybooking_app.tasks.generate_timeslots',
        'schedule': crontab(minute=0, hour=0),  # daily at midnight
    },
}