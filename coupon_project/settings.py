import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Parse allowed hosts from environment variable
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Add ngrok URL to allowed hosts if available
ngrok_url = os.environ.get('NGROK_URL')
if ngrok_url and ngrok_url not in ALLOWED_HOSTS:
    # Extract hostname from URL (remove protocol)
    ngrok_host = ngrok_url.split('//')[-1]
    ALLOWED_HOSTS.append(ngrok_host)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'corsheaders',
    'coupons',
    'analytics',
    'admin_panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'analytics.middleware.AnalyticsMiddleware',  
]

ROOT_URLCONF = 'coupon_project.urls'

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
                'coupons.context_processors.app_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'coupon_project.wsgi.application'

# Database configuration - SIMPLIFIED FOR SQLITE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Where collected static files go
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Your main static files directory
    BASE_DIR / 'coupon_project/static',  # Add if you have app-specific static files
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins if origin.strip()]

# Add ngrok URL to CORS if available
if ngrok_url:
    CORS_ALLOWED_ORIGINS.append(ngrok_url)

# CSRF settings for ngrok
CSRF_TRUSTED_ORIGINS = []
if ngrok_url:
    CSRF_TRUSTED_ORIGINS.append(ngrok_url)

# Login URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# Email settings
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', DEFAULT_FROM_EMAIL)

# SEO Settings
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

# Cache configuration
cache_backend = os.environ.get('CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache')
cache_location = os.environ.get('CACHE_LOCATION', 'unique-snowflake')

if cache_backend == 'django_redis.cache.RedisCache':
    redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')
    CACHES = {
        'default': {
            'BACKEND': cache_backend,
            'LOCATION': redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': cache_backend,
            'LOCATION': cache_location,
        }
    }

# Cache timeout settings (in seconds)
CACHE_TIMEOUT = {
    'short': 60 * 3,      # 3 minutes
    'medium': 60 * 10,    # 10 minutes
    'long': 60 * 60,      # 1 hour
}

# App Settings
APP_NAME = "CouPradise"
APP_TAGLINE = "Save Money with Exclusive Coupons"
APP_ICON = "fas fa-ticket-alt"
APP_FAVICON = "img/favicon.ico"
APP_LOGO = "img/logo.jpg"

# Social Media Links
SOCIAL_LINKS = {
    'twitter': 'https://twitter.com/coupradise',
    'facebook': 'https://facebook.com/coupradise',
    'instagram': 'https://instagram.com/coupradise',
}

# Contact Information
CONTACT_EMAIL = 'coupradise.deals@gmail.com'
CONTACT_PHONE = '+1 (555) 123-4567'