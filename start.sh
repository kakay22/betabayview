#!/bin/bash
# start.sh
gunicorn HMS.wsgi:application --bind 0.0.0.0:8000 --timeout 600
