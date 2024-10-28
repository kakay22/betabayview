# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import Maintenance_request, Notification
from django.utils import timezone
from ADMIN.models import Comment, Event, Announcement, VisitRequest
from USERS.models import HomeOwner
from django.contrib.auth.models import User
from django.utils import timezone


@receiver(post_save, sender=Maintenance_request)
def create_notification(sender, instance, created, **kwargs):
    # Get the current status of the maintenance request
    status = instance.status
    description = instance.Description_of_issue

    # Define notification messages and icons based on the status
    if status == 'Done':
        notification_message = f"Your maintenance request '{description}' has been completed. Click to verify and provide feedback."
        icon = "bi-check-circle"
    elif status == 'In progress':
        notification_message = f"Your maintenance request '{description}' is now in progress."
        icon = "bi-tools"
    elif status == 'Pending':
        notification_message = f"Your maintenance request '{description}' is pending approval."
        icon = "bi-hourglass-split"
    elif status == 'verified':
        notification_message = f"Your maintenance request '{description}' is verified."
        icon = "bi-check-circle"
    elif status == 'notverified':
        notification_message = f"Your maintenance request '{description}' is not verified."
        icon = "bi-x-circle"

    # Check if a notification already exists for this request and status
    if not Notification.objects.filter(maintenance_request=instance, message=notification_message).exists():
        # Create the notification
        Notification.objects.create(
            homeowner=instance.name_of_owner,
            message=notification_message,
            icon=icon,
            maintenance_request=instance,
            created_at=timezone.now(),
        )
        print(f"Notification created for request: {instance.id}")
    else:
        print(f"Notification already exists for request: {instance.id}")


from django.utils import timezone
from .models import Notification

def notify_max_request(homeowner, maintenance_request=None):
    # Create the notification
    notification = Notification.objects.create(
        homeowner=homeowner,
        icon='bi-exclamation-circle',  # You can customize this based on the type of notification
        message=f"You have reached your monthly limit (5/month) of maintenance requests.",
        is_read=False,  # Mark as unread by default
        created_at=timezone.now(),
        maintenance_request=None  # Can be null or the specific request causing the notification
    )
    notification.save()

# Signal for creating a notification when a new event is created
@receiver(post_save, sender=Event)
def send_event_notification(sender, instance, created, **kwargs):
    if created:
        # Fetch all homeowners with the role 'owner'
        homeowners = HomeOwner.objects.filter(role='owner')

        for homeowner in homeowners:
            # Create a notification for each homeowner
            Notification.objects.create(
                homeowner=homeowner.user,  # Assuming HomeOwner model has a foreign key to User
                icon='bi-calendar-event',  # You can set the icon as needed
                message=f"New event '{instance.event_name}' has been created. Don't miss out!",
                maintenance_request=None  # No link to maintenance in this case
            )


# Signal for creating a notification when a new announcement is created
@receiver(post_save, sender=Announcement)
def send_announcement_notification(sender, instance, created, **kwargs):
    if created:
        # Fetch all homeowners with the role 'owner'
        homeowners = HomeOwner.objects.filter(role='owner')

        for homeowner in homeowners:
            # Create a notification for each homeowner
            Notification.objects.create(
                homeowner=homeowner.user, 
                icon='bi-megaphone',  # You can set the icon as needed
                message=f"New announcement '{instance.title}' has been posted! \n '{instance.content}'",
                maintenance_request=None  # No link to maintenance in this case
            )

# Signal to create a notification when a VisitRequest is created for a homeowner
@receiver(post_save, sender=VisitRequest)
def send_visitor_request_notification(sender, instance, created, **kwargs):
    if created:
        # Fetch the homeowner associated with the visit request
        homeowner = instance.household_head

        # Create a notification specifically for this homeowner
        Notification.objects.create(
            homeowner=homeowner.user, 
            visit_request=instance,
            icon='bi-person-check',  # Icon specific for visitor requests
            message=(
                f"Visit request from {instance.visitor_full_name} "
                f"({instance.visitor_relation}) scheduled for {instance.visit_date.strftime('%B %d, %Y %I:%M %p')}. "
                "Please review and confirm the visit."
            ),
            maintenance_request=None  # No link to maintenance in this case
        )
