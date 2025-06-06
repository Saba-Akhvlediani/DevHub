import os
import sys
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Add apps directory to Python path
sys.path.append(os.path.join(BASE_DIR, 'apps'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # For PostgreSQL full-text search
]

THIRD_PARTY_APPS = [
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.common',
    'apps.accounts',
    'apps.categories',
    'apps.products.apps.ProductsConfig',
    'apps.cart',
    'apps.orders',
    'apps.payments',
    'apps.api',
    'apps.notifications',
    'apps.recommendations',
    'apps.inventory',
    'apps.dashboard',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'apps.common.middleware.SecurityHeadersMiddleware',
    'apps.common.middleware.RateLimitMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # For Georgian language support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.common.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # For language support
                'django.template.context_processors.media',  # For media files in templates
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = config('LANGUAGE_CODE', default='ka-ge')
TIME_ZONE = config('TIME_ZONE', default='Asia/Tbilisi')
USE_I18N = True
USE_TZ = True

# Languages supported by your site
LANGUAGES = [
    ('ka', 'Georgian'),
    ('en', 'English'),
]

# Locale paths for translations
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = config('STATIC_URL', default='/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (User uploaded content)
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model (if you plan to extend User model later)
# AUTH_USER_MODEL = 'accounts.CustomUser'

# Email configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@georgianequipment.ge')
SERVER_EMAIL = config('SERVER_EMAIL', default='server@georgianequipment.ge')

# Site configuration
SITE_NAME = config('SITE_NAME', default='Georgian Equipment')
SITE_URL = config('SITE_URL', default='http://localhost:8000')
DEFAULT_CURRENCY = config('DEFAULT_CURRENCY', default='₾')

# Session configuration
SESSION_COOKIE_AGE = 86400 * 7  # 1 week
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Cart session key
CART_SESSION_ID = 'cart'

# Pagination settings
PRODUCTS_PER_PAGE = 12
ORDERS_PER_PAGE = 10

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Cache configuration (Redis for production, database for development)
CACHES = {
    'default': {
        'BACKEND': config(
            'CACHE_BACKEND', 
            default='django.core.cache.backends.db.DatabaseCache'
        ),
        'LOCATION': config('CACHE_LOCATION', default='cache_table'),
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# CORS settings (for frontend/mobile apps)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Payment Gateway Configuration
# TBC Bank
TBC_CLIENT_ID = config('TBC_CLIENT_ID', default='')
TBC_CLIENT_SECRET = config('TBC_CLIENT_SECRET', default='')
TBC_SANDBOX_MODE = config('TBC_SANDBOX_MODE', default=True, cast=bool)

# Bank of Georgia
BOG_CLIENT_ID = config('BOG_CLIENT_ID', default='')
BOG_CLIENT_SECRET = config('BOG_CLIENT_SECRET', default='')
BOG_SANDBOX_MODE = config('BOG_SANDBOX_MODE', default=True, cast=bool)

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule (for periodic tasks)
CELERY_BEAT_SCHEDULE = {
    'send-abandoned-cart-emails': {
        'task': 'apps.notifications.tasks.send_abandoned_cart_emails',
        'schedule': 86400.0,  # Run daily
    },
    'send-scheduled-campaigns': {
        'task': 'apps.notifications.tasks.send_scheduled_campaigns',
        'schedule': 3600.0,  # Run hourly
    },
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.common.middleware': {
            'handlers': ['security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.recommendations': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.notifications': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Rate Limiting Settings
RATE_LIMIT_ENABLE = config('RATE_LIMIT_ENABLE', default=True, cast=bool)

# Search Configuration
# Minimum characters for search suggestions
SEARCH_MIN_LENGTH = 2
# Maximum search results per page
SEARCH_MAX_RESULTS = 50

# Recommendation Engine Settings
RECOMMENDATION_CACHE_TIMEOUT = 3600  # 1 hour
RECOMMENDATION_MAX_ITEMS = 10

# Inventory Settings
LOW_STOCK_THRESHOLD = 10
REORDER_POINT_THRESHOLD = 5
SAFETY_STOCK_DAYS = 7

# File Upload Settings
# Maximum file size for product images (in bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
# Allowed image formats
ALLOWED_IMAGE_FORMATS = ['JPEG', 'PNG', 'WebP']

# Admin Configuration
ADMIN_URL = config('ADMIN_URL', default='admin/')

# API Versioning
API_VERSION = 'v1'

# Feature Flags
FEATURES = {
    'RECOMMENDATIONS': config('FEATURE_RECOMMENDATIONS', default=True, cast=bool),
    'EMAIL_CAMPAIGNS': config('FEATURE_EMAIL_CAMPAIGNS', default=True, cast=bool),
    'INVENTORY_MANAGEMENT': config('FEATURE_INVENTORY', default=True, cast=bool),
    'ADVANCED_SEARCH': config('FEATURE_ADVANCED_SEARCH', default=True, cast=bool),
}