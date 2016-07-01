from .base import *

DEBUG = False

ALLOWED_HOSTS = ['163.172.167.163', 'tweets.mikexine.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tweets',
        'USER': 'collector',
        'PASSWORD': 'c0llect0r',
        'HOST': 'localhost',
        'PORT': '',
    }
}


# PYTHON_EXECUTABLE = '/srv/django-envs/tweetset/bin/python'

PROJECT_ROOT = '/home/mikexine/tweetset/tweetset/'

STATICFILES_DIRS = (
    PROJECT_ROOT + 'collect/static/',
)
