"""
Django settings for AnalyticsforSpotify project.

Generated by 'django-admin startproject' using Django 3.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""


import os
import sys
import logging


class FilenameLinenoFilter(logging.Filter):
    # https://stackoverflow.com/questions/35278607/how-to-set-width-of-combined-fields-in-python-logging
    def filter(self, record):
        record.filename_lineno = '{}.{}:{}'.format(
            record.name, record.funcName, record.lineno)
        return True


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'LocalAcessOnly'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'webBackend.apps.WebBackendConfig',
    'django_nose',
]

# Use nose to run all tests
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Tell nose to measure coverage on the 'foo' and 'bar' apps
NOSE_ARGS = [
    '--with-coverage',
    '--cover-package=webBackend',
    '--cover-package=songMonitoringBackend',
    '--cover-html',
]

MIDDLEWARE = [
    # https://stackoverflow.com/a/30956822
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Local Only Acesss 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
CORS_ORIGIN_ALLOW_ALL = True


ROOT_URLCONF = 'AnalyticsforSpotify.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
        'OPTIONS': {
            'read_default_file':  BASE_DIR + '/AnalyticsforSpotify/my.cnf',
        },
    }
}
WSGI_APPLICATION = 'AnalyticsforSpotify.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'filename_lineno_filter': {
            '()': FilenameLinenoFilter,
        },
    },
    'formatters': {
        'default': {
            'format': '%(filename_lineno)-45s %(levelname)-8s  %(message)s',
        },
        'file': {
            'format': '%(asctime)-20s %(filename_lineno)-45s %(levelname)-8s  %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['filename_lineno_filter'],
            'formatter': 'default',
            'stream': sys.stdout
        },
        'file': {
            'class': 'logging.FileHandler',
            'filters': ['filename_lineno_filter'],
            'formatter': 'file',
            'filename': os.path.join(BASE_DIR, "analytics-for-spotify.log"),
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Detroit'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400

STATIC_URL = '/spotify/'

STATIC_ROOT = os.path.join(BASE_DIR, "webFrontend")
