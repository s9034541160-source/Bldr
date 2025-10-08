import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Celery app instance
celery_app = Celery(
    'bldr_empire',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['core.celery_norms']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    beat_schedule={
        'daily-norms-update': {
            'task': 'core.celery_norms.update_norms_task',
            'schedule': 86400.0,  # Daily
            'args': (['construction', 'finance'], False),
        },
    },
)

if __name__ == '__main__':
    celery_app.start()