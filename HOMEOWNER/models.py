from django.db import models
from USERS.models import HomeOwner
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.apps import apps  # Import apps to use get_model


# Create your models here.
class Maintenance_request(models.Model):
    name_of_owner = models.ForeignKey(User, on_delete=models.CASCADE)
    Description_of_issue = models.TextField()
    type_of_issue = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=255, blank=True, default='Pending')
    date_requested = models.DateTimeField(auto_now_add=True)  # Automatically set to the current date
    date_resolved = models.DateTimeField(null=True, blank=True)  # Automatically set to the current date
    repairman = models.CharField(max_length=255)
    feedback = models.TextField(blank=True, null=True)  # New field for feedback
    image = models.ImageField(default="req_maintenance.jpg", blank=True, null=True)  # New field for feedback
    property = models.ForeignKey('ADMIN.Property', on_delete=models.CASCADE, null=True, blank=True)  # Foreign key to Property model

    def __str__(self):
        return f"{self.name_of_owner} - {self.type_of_issue} - {self.status}"

class Activitie(models.Model):
	name_of_owner = models.ForeignKey(User, on_delete=models.CASCADE)
	name_of_activity = models.CharField(max_length=255)
	date = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name_of_activity

class Notification(models.Model):
	homeowner = models.ForeignKey(User, on_delete=models.CASCADE)
	icon = models.CharField(max_length=255, default='bi-info-circle')
	message = models.TextField()
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(default=timezone.now)
	maintenance_request = models.ForeignKey(
        Maintenance_request, 
        on_delete=models.CASCADE, 
        null=True,  # Allow the field to be null
        blank=True  # Allow the field to be empty
    )
	notif_url = models.URLField(max_length=255, null=True, blank=True)  # Add the notif_url field

	def __str__(self):
		return self.message
	