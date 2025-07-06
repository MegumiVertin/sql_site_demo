"""
Django settings for sql_site project – production‑ready version.
Read environment variables for secrets & host‑specific values.
Compatible with platforms like Render.com, Railway, Fly.io, or a VPS.
"""

from pathlib import Path
import os
import dj_database_url  # pip install dj-database-url

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------------
# Core security & debug
# ----------------------------------------------------------------------------
# SECRET_KEY **must** be set in your hosting platform's env vars
SECRET_KEY: str = os.getenv("DJANGO_SECRET_KEY", "unsafe‑dev‑key‑replace‑me")

# DEBUG should be False in prod; enable True locally with `export DJANGO_DEBUG=True`
DEBUG: bool = os.getenv("DJANGO_DEBUG", "False").lower() in {"1", "true", "yes"}

# Comma‑separated hosts, e.g. "example.com,www.example.com"
ALLOWED_HOSTS: list[str] = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Trust CSRF from Render / Fly preview domains etc.
CSRF_TRUSTED_ORIGINS: list[str] = [
    f"https://{h}" for h in ALLOWED_HOSTS if not (h.startswith("127.") or h == "localhost")
]

# ----------------------------------------------------------------------------
# Applications
# ----------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third‑party
    "whitenoise.runserver_nostatic",  # keep before django.contrib.staticfiles

    # local apps
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve static files efficiently
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sql_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sql_site.wsgi.application"

# ----------------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------------
# Tries DATABASE_URL first (e.g. "postgres://user:pass@host:5432/db")
# Falls back to local SQLite for dev.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# ----------------------------------------------------------------------------
# Password validation
# ----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------------------------------------------------
# Internationalization
# ----------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TZ", "UTC")
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------------------------------
# Static & media files
# ----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # folder where collectstatic puts files

# Additional static dirs for local dev (ignored on prod if not present)
STATICFILES_DIRS = [BASE_DIR / "static"]

# Whitenoise: enable compression & long‑cache headers
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ----------------------------------------------------------------------------
# Security hardening (only active when DEBUG=False)
# ----------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", 86400))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "same-origin"

# ----------------------------------------------------------------------------
# Misc
# ----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Toggle demo / real API mode (example custom flag)
DEMO_MODE = os.getenv("DEMO_MODE", "False").lower() in {"1", "true", "yes"}
