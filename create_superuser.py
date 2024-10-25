import os
import django

# Set up Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HMS.settings")
django.setup()

from django.contrib.auth.models import User

# Update these values as needed
admin_username = "admin"  # Change this to your desired username
admin_email = "bbvhhousingmanagement@gmail.com"  # Change this to your desired email
admin_password = "admin@2024"  # Change this to your desired password

# Check if the admin user already exists, if not, create one
if not User.objects.filter(username=admin_username).exists():
    User.objects.create_superuser(admin_username, admin_email, admin_password)
    print("Superuser created successfully")
else:
    print("Superuser already exists")
