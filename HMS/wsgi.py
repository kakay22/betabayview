import os
from django.core.wsgi import get_wsgi_application
import download_resources  # Ensure this is the correct import based on your file structure

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings.production')

application = get_wsgi_application()
