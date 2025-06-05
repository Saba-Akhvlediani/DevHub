from .base import *
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Development-specific installed apps
INSTALLED_APPS += [
    'django_extensions',  # Optional: for development tools
]

# Database for development
# Uses the same database config from base.py but you can override if needed
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# Email backend for development (prints emails to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development cache (dummy cache - no caching)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Development logging - more verbose
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Create logs directory if it doesn't exist
import os
if not os.path.exists(BASE_DIR / 'logs'):
    os.makedirs(BASE_DIR / 'logs')

# Development-specific middleware
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Optional: Add Django Debug Toolbar for development
# Uncomment if you install django-debug-toolbar
# if DEBUG:
#     INSTALLED_APPS += ['debug_toolbar']
#     MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Development payment settings (use sandbox/test environments)
TBC_CLIENT_ID = config('TBC_CLIENT_ID', default='test-client-id')
TBC_CLIENT_SECRET = config('TBC_CLIENT_SECRET', default='test-client-secret')
TBC_SANDBOX_MODE = True

BOG_CLIENT_ID = config('BOG_CLIENT_ID', default='test-client-id')
BOG_CLIENT_SECRET = config('BOG_CLIENT_SECRET', default='test-client-secret')
BOG_SANDBOX_MODE = True

# Development file serving
# Django will serve media files in development
# In production, this should be handled by nginx/apache
if DEBUG:
    import os
    from django.conf.urls.static import static
    from django.conf import settings