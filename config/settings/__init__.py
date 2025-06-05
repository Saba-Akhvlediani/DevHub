"""
Django settings module initialization.

This file determines which settings module to use based on the DJANGO_SETTINGS_MODULE
environment variable or defaults to development settings.
"""

import os
from decouple import config

# Determine which settings module to use
ENVIRONMENT = config('ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'development':
    from .development import *
else:
    from .development import *  # default to development