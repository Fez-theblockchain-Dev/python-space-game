"""
Django settings for Space Cowboys🚀 Store landing page.
"""
import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(env_path: Path) -> None:
    """Load simple KEY=VALUE pairs from a local .env file."""
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            os.environ.setdefault(key, value)


load_env_file(BASE_DIR / ".env")

# Security settings
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() == 'true'

# Hosts allowed to reach this Django app.  Production always includes the
# Vercel domain; additional hosts (staging, preview deploys) can be added
# via DJANGO_ALLOWED_HOSTS (comma-separated).
DEFAULT_ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'spacecowboys.dev',
    'www.spacecowboys.dev',
    '.spacecowboys.dev',
    '.vercel.app',
]

extra_hosts = os.getenv('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = list(DEFAULT_ALLOWED_HOSTS)
if extra_hosts:
    ALLOWED_HOSTS.extend(host.strip() for host in extra_hosts.split(',') if host.strip())

# POST/PUT/DELETE from the Vercel-hosted pages must pass the CSRF origin
# check.  Without this, Django returns 403 for every non-GET request that
# originates from https://spacecowboys.dev.  Localhost entries cover the
# unified dev entry point on the pygbag port (9666) plus a Django-only
# alternate port (9000) for when you want the storefront standalone.
CSRF_TRUSTED_ORIGINS = [
    'https://spacecowboys.dev',
    'https://www.spacecowboys.dev',
    'https://*.spacecowboys.dev',
    'https://*.vercel.app',
    'http://localhost:9666',
    'http://localhost:9000',
    'http://127.0.0.1:9666',
    'http://127.0.0.1:9000',
]

extra_trusted = os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '')
if extra_trusted:
    CSRF_TRUSTED_ORIGINS.extend(
        origin.strip() for origin in extra_trusted.split(',') if origin.strip()
    )

# Behind Vercel's TLS terminator Django sees HTTP, not HTTPS.  Trust the
# X-Forwarded-Proto header the proxy sets so request.is_secure() is correct
# and CSRF / cookie flags line up.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# In production (DEBUG off) require secure cookies and HTTPS redirects.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'webApp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'webApp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'webApp' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'webApp.context_processors.social_links',
            ],
        },
    },
]

WSGI_APPLICATION = 'webApp.wsgi.application'

# Database (minimal configuration for static file serving)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'webApp' / 'static']

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
# Support both the correct variable name and legacy misspelling.
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY') or os.getenv('STRIPE_SECRETE_API_KEY', '')

STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Backend API URL (FastAPI server).  In production this should point to
# https://api.spacecowboys.dev; locally it sits on the unified pygbag port
# (9666) so dev only has one URL to remember.
BACKEND_API_URL = os.getenv(
    'BACKEND_API_URL',
    'https://api.spacecowboys.dev' if not DEBUG else 'http://localhost:9666',
)

# Canonical public origin for the Vercel-hosted frontend -- referenced by
# Stripe return URLs, social share cards, etc.
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'https://spacecowboys.dev')

