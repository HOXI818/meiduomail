from celery import Celery

# 设置Django运行所依赖环境变量
import os
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

celery_app = Celery("celery_tasks")

celery_app.config_from_object('celery_tasks.config')

celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])