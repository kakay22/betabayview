# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import SecNotification
from ADMIN.models import Comment, Event, AnnouncementComment
from USERS.models import HomeOwner
from HOMEOWNER.models import Maintenance_request
from django.contrib.auth.models import User
from django.utils import timezone

def create_homeowner_notification(homeowner):
     # Use filter to get all staff users (secretaries)
    secretaries = User.objects.filter(is_staff=True).distinct()

    # Create the URL for the pending accounts page
    pending_accounts_url = reverse('sec_pending_accounts')

    # Create the message with the link
    message = f"""
            <a href="{pending_accounts_url}">
                A new account has been created for <span class="font-bold">{homeowner.user.first_name}</span> and is pending approval.
            </a>
        """

    # Iterate over each secretary and create a notification
    for secretary in secretaries:
        SecNotification.objects.create(
            secretary=secretary,
            icon="bi-person-badge",
            message=message,
            created_at=timezone.now(),
            is_read=False,
        )


def create_maintenance_request_notification(maintenance_request):
    # Get all secretaries (staff users)
    secretaries = User.objects.filter(is_staff=True).distinct()

    # Check if secretaries exist
    if secretaries.exists():
        # Loop through each secretary and create a notification
        for secretary in secretaries:
            # Create the URL for the maintenance request list page
            maintenance_request_url = reverse('sec_maintenance_request_list')

            # Create the message with the homeowner's first name and the issue description
            message = f"""
                <a href="{maintenance_request_url}">
                    <span class="font-bold">{maintenance_request.name_of_owner.first_name}</span> has requested maintenance:
                    <span class="font-bold">"{maintenance_request.Description_of_issue}"</span>.
                </a>
            """

            # Create the notification for each secretary
            SecNotification.objects.create(
                secretary=secretary,
                icon="bi-wrench",
                message=message,
                created_at=timezone.now(),
                is_read=False,
            )
    else:
        # Handle the case where no secretaries are found, if needed
        print("No secretaries found.")


def create_verified_notification(maintenance_req):
    # Get all secretaries (staff users)
    secretaries = User.objects.filter(is_staff=True).distinct()

    # Check if secretaries exist
    if secretaries.exists():
        # Loop through each secretary and create a notification
        for secretary in secretaries:
            # Create the URL for the maintenance request list page
            maintenance_request_url = reverse('sec_maintenance_request_list')

            # Create the message with the homeowner's first name, issue description, and feedback
            message = f"""
                <a href="{maintenance_request_url}">
                    {maintenance_req.name_of_owner.first_name} has marked the maintenance:
                    "<span class="font-bold">{maintenance_req.Description_of_issue}</span>" as <span class="text-green-500 font-medium">{maintenance_req.status}</span>.
                    <p class="text-sm text-gray-500">Feedback: "{maintenance_req.feedback}"</p>
                </a>
            """

            # Create the notification for each secretary
            SecNotification.objects.create(
                secretary=secretary,
                icon="bi-check-circle",
                message=message,
                created_at=timezone.now(),
                is_read=False,
            )
    else:
        # Handle the case where no secretaries are found, if needed
        print("No secretaries found.")

def create_not_verified_notification(maintenance_req):
    # Get all secretaries (staff users)
    secretaries = User.objects.filter(is_staff=True).distinct()

    # Check if secretaries exist
    if secretaries.exists():
        # Loop through each secretary and create a notification
        for secretary in secretaries:
            # Create the URL for the maintenance request list page
            maintenance_request_url = reverse('sec_maintenance_request_list')

            # Create the message with the homeowner's first name, issue description, and feedback
            message = f"""
                <a href="{maintenance_request_url}">
                    {maintenance_req.name_of_owner.first_name} has marked the maintenance:
                    "<span class="font-bold">{maintenance_req.Description_of_issue}</span>" as <span class="text-red-500 font-medium">{maintenance_req.status}</span>.
                    <p class="text-sm text-gray-500">Feedback: "{maintenance_req.feedback}"</p>
                </a>
            """

            # Create the notification for each secretary
            SecNotification.objects.create(
                secretary=secretary,
                icon="bi-x-circle",
                message=message,
                created_at=timezone.now(),
                is_read=False,
            )
    else:
        # Handle the case where no secretaries are found, if needed
        print("No secretaries found.")


@receiver(post_save, sender=AnnouncementComment)
def send_comment_notification(sender, instance, created, **kwargs):
    if created:
        # Get all users with admin privileges
        sec_users = User.objects.filter(is_staff=True)
        pending_accounts_url = reverse('sec_announcements')

        # Create a notification for each admin
        for sec in sec_users:
             message = f"""
                    <a href="{pending_accounts_url}">
                        {instance.user.username} commented on the announcement <span class='font-bold'>'{instance.announcement.title}'<span>
                    </a>
                """
        SecNotification.objects.create(
                secretary=sec,
                icon="bi-chat-left-text",  # An icon representing a comment, adjust as needed
                message=message,
                created_at=timezone.now(),
                is_read=False,
            )