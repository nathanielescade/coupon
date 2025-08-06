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
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'True'

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
                'coupons.context_processors.app_settings',  # Add this line
            ],
        },
    },
]

WSGI_APPLICATION = 'coupon_project.wsgi.application'

# Database
# Use DATABASE_URL if available, otherwise use SQLite
DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}')

# Default to SQLite if no DATABASE_URL is provided
if DATABASE_URL.startswith('sqlite'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / DATABASE_URL.replace('sqlite:///', ''),
        }
    }
elif DATABASE_URL.startswith('postgres'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    # Fallback to SQLite
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
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

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
CORS_ALLOWED_ORIGINS = cors_origins

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

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Email settings
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', DEFAULT_FROM_EMAIL)

# SEO Settings
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

# Sitemap Settings
TEMPLATES[0]['OPTIONS']['context_processors'].append('django.template.context_processors.request')

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
APP_NAME = "CouponHub"
APP_TAGLINE = "Save Money with Exclusive Coupons"
APP_ICON = "fas fa-ticket-alt"
APP_FAVICON = "img/couponhub.ico"
APP_LOGO = "img/couponhub.jpg"

# Social Media Links
SOCIAL_LINKS = {
    'twitter': 'https://twitter.com/couponhub',
    'facebook': 'https://facebook.com/couponhub',
    'instagram': 'https://instagram.com/couponhub',
}

# Contact Information
CONTACT_EMAIL = 'support@couponhub.com'
CONTACT_PHONE = '+1 (555) 123-4567'