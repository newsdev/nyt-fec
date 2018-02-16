import os

from config.dev.settings import *

DEBUG = True
WSGI_APPLICATION = 'config.stg.app.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', None),
        'USER': os.environ.get('DB_USER', None),
        'PASSWORD': os.environ.get('DB_PASSWORD', None),
        'HOST': os.environ.get('DB_HOST', None),
    }
}

ALLOWED_HOSTS = ['*']

AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_S3_CUSTOM_DOMAIN = os.environ.get('S3_BUCKET_DOMAIN', 'int.stg.nyt.com')
AWS_STORAGE_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'int.stg.nyt.com')
AWS_S3_SECURE_URLS = True
AWS_S3_URL_PROTOCOL = 'https:'
