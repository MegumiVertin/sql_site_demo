"""
WSGI config for sql_site project.

It exposes the WSGI callable as a module-level variable named ``application``.
For details, see https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Ensure the correct settings module is loaded
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sql_site.settings")

application = get_wsgi_application()
