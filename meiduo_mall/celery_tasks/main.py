from celery import Celery

celery_app = Celery("celery_tasks")

celery_app.config_from_object('celery_tasks.config')

celery_app.autodiscover_tasks(['celery_tasks.sms'])