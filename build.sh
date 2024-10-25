#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Install requirements
pip install -r requirements.txt

# Download NLTK resources
python download_resources.py

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput
