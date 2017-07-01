import logging

import os

# Django settings for cookingsite project.
from django.conf import global_settings
import socket
hostname = socket.gethostname()

DEFAULT_CHARSET="utf-8"

RECIPES_COLLECTION_PREFIX=""

DEBUG = True
RECIPES_COLLECTION_PREFIX="/home/thorben/code/example_gourmet_recipes"

ADMINS = (
    ('Thorben Kroeger', 'dev@thorben.net'),
)

ALLOWED_HOSTS = [u'localhost', u'127.0.0.1']

MANAGERS = ADMINS

template_path = os.path.abspath(os.path.join(os.path.basename(__file__), "..", "templates"))
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [template_path],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cookingsite',
        'USER': 'cookingsite',
        'PASSWORD': 'cookingsite_password',
        'HOST': '', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '', # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': { 'init_command': 'SET default_storage_engine=INNODB' }
    }
}

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de'

SITE_ID = 1

USE_I18N = False
USE_L10N = True
USE_TZ = True
MEDIA_URL = ''
STATIC_ROOT = ''
STATIC_URL = '/static/'

static_path = os.path.abspath(os.path.join(os.path.basename(__file__), "..", "static"))
STATICFILES_DIRS = (
    static_path,
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '*ou8uhcn+4&amp;#7y&amp;_@3mb0=x5s^urze%e$g+#(vi2^0hyp@jx!='

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)

ROOT_URLCONF = 'cookingsite.urls'

LOGIN_REDIRECT_URL='/'

WSGI_APPLICATION = 'cookingsite.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'recipes',
    'django.contrib.admin',
    'django.contrib.admindocs'
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
