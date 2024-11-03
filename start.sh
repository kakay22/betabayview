#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Activate the virtual environment
source venv/bin/activate  # Adjust the path as necessary

# Download the VADER lexicon
python -m nltk.downloader vader_lexicon

# Set the DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE=HMS.settings.production

# Run Django migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if it doesn't already exist
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'bbvhhousingmanagement@gmail.com', 'admin@2024')
EOF

# Start the Django application
gunicorn HMS.wsgi --log-file -
