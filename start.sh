#!/bin/bash
export DJANGO_SETTINGS_MODULE=HMS.settings.production
gunicorn HMS.wsgi:application --bind 0.0.0.0:8000

python -m nltk.downloader vader_lexicon
