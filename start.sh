#!/bin/bash

# Activate the virtual environment
source venv/bin/activate  # Adjust the path as necessary

# Download the VADER lexicon
python -m nltk.downloader vader_lexicon

# Set the DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE=HMS.settings.production

# Start the Django application
gunicorn HMS.wsgi --log-file -
