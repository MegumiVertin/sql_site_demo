import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sql_site.settings")

app = Celery("mysite")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
