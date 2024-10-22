import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings')  # Replace with your project name

application = get_wsgi_application()
