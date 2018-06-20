import os

from config.dev.settings import *

DEBUG = False
WSGI_APPLICATION = 'config.prd.app.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', 'fec_prd'),
        'USER': os.environ.get('DB_USER', 'fec_prd'),
        'PASSWORD': os.environ.get('DB_PASSWORD', None),
        'HOST': os.environ.get('DB_HOST', None),
    }
}

ALLOWED_HOSTS = ['*']

AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_S3_CUSTOM_DOMAIN = os.environ.get('S3_BUCKET_DOMAIN', 'int.nyt.com')
AWS_STORAGE_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'int.nyt.com')
AWS_S3_SECURE_URLS = True
AWS_S3_URL_PROTOCOL = 'https:'

DATADOG_API_KEY = os.environ.get('DATADOG_API_KEY')
DATADOG_APP_KEY = os.environ.get('DATADOG_APP_KEY')


if not (DATADOG_API_KEY and DATADOG_APP_KEY):
    print("{}: datadog credentials missing")
try:
    options = {
        'api_key':DATADOG_API_KEY,
        'app_key':DATADOG_APP_KEY
    }
    initialize(**options)
except Exception as e:
    print("{}: failed to intialize datadog")

