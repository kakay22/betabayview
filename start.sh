#!/bin/bash
# start.sh
export DJANGO_SETTINGS_MODULE=HMS.settings.production
gunicorn HMS.wsgi:application --bind 0.0.0.0:8000 --timeout 600
