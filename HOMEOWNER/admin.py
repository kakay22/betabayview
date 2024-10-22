from django.contrib import admin
from .models import Maintenance_request, Activitie, Notification

# Register your models here.
admin.site.register(Maintenance_request)
admin.site.register(Activitie)
admin.site.register(Notification)
