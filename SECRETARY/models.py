from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SecNotification(models.Model):
    ICON_CHOICES = [
        ('info', 'bi-info-circle'),
        ('pending_account', 'bi-person-badge'),
        ('maintenance', 'bi-wrench'),
        # Add more icon choices as needed
    ]

    secretary = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='info')  # New icon field

    def __str__(self):
        return self.message
