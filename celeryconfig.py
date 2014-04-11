# setup celery
BROKER_URL = 'redis://localhost:6379/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}  # 1 hour.
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE = 'utc'
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'US/Eastern'
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    # Executes every Monday morning at 7:30 A.M
    'xbox-titles-weekly': {
        'task': 'nat.tasks.xbox_titles',
        'schedule': crontab(hour=20, minute=34, day_of_week='wed'),
        'args': (),
    },
}
