import os
import django

# Set up Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HMS.settings")
django.setup()

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Check if the admin user already exists, if not, create one
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser("admin", "admin@example.com", "your_password_here")
    print("Superuser created successfully")
else:
    print("Superuser already exists")
