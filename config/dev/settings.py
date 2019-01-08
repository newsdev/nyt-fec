import os
from boto.s3.connection import ProtocolIndependentOrdinaryCallingFormat
from datadog import initialize, api


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#this is a garbage secret key for dev, the actual key is set in env vars
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '++hv#e)wqd-as;dlkjf;sdkfljsfdg3499134mndfs!@^$-snmz+@m(&-g5e74&zg)+geh-xqe')
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django.contrib.humanize',
    'rest_framework',
    'pure_pagination',
    'storages',
    'cycle_2018'
]

MIDDLEWARE = [
    'middleware.HealthCheckMiddleware',
    'middleware.TimezoneMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['cycle_2018/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.static',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.dev.app.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('fec_DB_NAME', 'fec'),
        'USER': os.environ.get('fec_DB_USER', ''),
        'PASSWORD': os.environ.get('fec_DB_PASSWORD', ''),
        'HOST': os.environ.get('fec_DB_HOST', ''),
    }
}

ADD_REVERSION_ADMIN=True

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

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

PAGINATION_SETTINGS = {
    'PAGE_RANGE_DISPLAYED': 4,
    'MARGIN_PAGES_DISPLAYED': 1,
    'SHOW_FIRST_PAGE_WHEN_INVALID': True,
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

AWS_S3_CALLING_FORMAT = ProtocolIndependentOrdinaryCallingFormat()
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_STORAGE_BUCKET_NAME = os.environ.get('fec_S3_BUCKET_NAME', 'int.dev.nyt.com')
AWS_S3_CUSTOM_DOMAIN = os.environ.get('fec_S3_BUCKET_DOMAIN', 'int.dev.nyt.com')
AWS_S3_SECURE_URLS = False
AWS_S3_URL_PROTOCOL = 'http:'

STATICFILES_LOCATION = 'apps/fec'
STATICFILES_STORAGE = 'utils.custom_storages.StaticStorage'
STATIC_URL = "%s/" % STATICFILES_LOCATION

MEDIAFILES_LOCATION = 'apps/fec/media'
MEDIA_URL = "%s/" % MEDIAFILES_LOCATION
DEFAULT_FILE_STORAGE = 'utils.custom_storages.MediaStorage'

#contact email address for the person/team currently responsible for the app.
CONTACT = os.environ.get('CONTACT')
