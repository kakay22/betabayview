# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from ADMIN.models import Comment, Event, Property
from USERS.models import HomeOwner
from HOMEOWNER.models import Maintenance_request
from django.contrib.auth.models import User
from django.utils import timezone
from .models import AdminNotification, AnnouncementComment

def admin_create_homeowner_notification(homeowner):
    # Get all superuser admins
    admins = User.objects.filter(is_superuser=True)  # Adjust if you have specific roles for admins
    
    # Create the URL for the pending accounts page
    pending_accounts_url = reverse('pending_accounts')  # Ensure this matches your URL pattern for pending accounts
    
    # Create the message with a link to the pending accounts page
    message = f"""
            <a href="{pending_accounts_url}">
                A new account has been created for <span class="font-bold">{homeowner.user.first_name}</span> and is pending approval.
            </a>
        """
    
    # Create notifications for all admins
    for admin in admins:
        AdminNotification.objects.create(
            admin=admin,  # Assuming 'admin' field is a ForeignKey to the User model
            icon="bi-person-badge",  # Bootstrap icon class
            message=message,  # Notification message with a link
            created_at=timezone.now(),  # Current timestamp
            is_read=False  # Mark as unread by default
        )

def admin_create_maintenance_request_notification(maintenance_request):
    try:
        # Assuming you have a way to get the secretary user
        admin = User.objects.get(is_superuser=True)  # Modify this as needed
    except User.DoesNotExist:
        # Handle the case where no secretary is found, if needed
        return

    # Create the URL for the maintenance request list page
    maintenance_request_url = reverse('maintenance_request_list')

    owner = maintenance_request.name_of_owner
    homeowner = HomeOwner.objects.get(user=owner)
    property = Property.objects.get(household_head=homeowner)
    
    # Create the message with the homeowner's first name and the issue description
    message = f"""
        <a href="{maintenance_request_url}">
            <span class="font-bold">{maintenance_request.name_of_owner.first_name}</span> has requested maintenance: 
            <span class="font-bold">"{maintenance_request.Description_of_issue} for <span class="font-bold">{property.property_name}</span> "</span>.
        </a>
    """
    
    # Create the notification
    AdminNotification.objects.create(
        admin=admin,
        icon="bi-wrench",
        message=message,
        created_at=timezone.now(),
        is_read=False,
    )


def admin_create_verified_notification(maintenance_req):
    try:
        # Assuming you have a way to get the secretary user
        admin = User.objects.get(is_superuser=True)  # Modify this as needed
    except User.DoesNotExist:
        # Handle the case where no secretary is found, if needed
        return

    # Create the URL for the maintenance request list page
    maintenance_request_url = reverse('maintenance_request_list')
    
     # Create the message with the homeowner's first name and the issue description
    message = f"""
        <a href="{maintenance_request_url}">
            {maintenance_req.name_of_owner.first_name} has marked the maintenance: 
            "<span class="font-bold">{maintenance_req.Description_of_issue}</span>" as <span class="text-green-500 font-medium">{maintenance_req.status}</span>.
            <p class="text-sm text-gray-500">Feedback: "{maintenance_req.feedback}"</p>
        </a>
    """
    
    # Create the notification
    AdminNotification.objects.create(
        admin=admin,
        icon="bi-check-circle",
        message=message,
        created_at=timezone.now(),
        is_read=False,
    )


def admin_create_not_verified_notification(maintenance_req):
    try:
        # Assuming you have a way to get the secretary user
        admin = User.objects.get(is_superuser=True)  # Modify this as needed
    except User.DoesNotExist:
        # Handle the case where no secretary is found, if needed
        return

    # Create the URL for the maintenance request list page
    maintenance_request_url = reverse('maintenance_request_list')
    
    # Create the message with the homeowner's first name and the issue description
    message = f"""
        <a href="{maintenance_request_url}">
            {maintenance_req.name_of_owner.first_name} has marked the maintenance: 
            "<span class="font-bold">{maintenance_req.Description_of_issue}</span>" as <span class="text-red-500 font-medium">{maintenance_req.status}</span>.
            <p class="text-sm text-gray-500">Feedback: "{maintenance_req.feedback}"</p>
        </a>
    """

    # Create the notification
    AdminNotification.objects.create(
        admin=admin,
        icon="bi-x-circle",
        message=message,
        created_at=timezone.now(),
        is_read=False,
    )

@receiver(post_save, sender=AnnouncementComment)
def send_comment_notification(sender, instance, created, **kwargs):
    if created:
        # Get all users with admin privileges
        admin_users = User.objects.filter(is_staff=True)

        pending_accounts_url = reverse('admin_announcements')

        # Create a notification for each admin
        for admin in admin_users:
            message = f"""
                    <a href="{pending_accounts_url}">
                        {instance.user.username} commented on the announcement <span class='font-bold'>'{instance.announcement.title}'<span>
                    </a>
                """

            AdminNotification.objects.create(
                admin=admin,
                icon="bi-chat-left-text",  # An icon representing a comment, adjust as needed
                message=message,
                created_at=timezone.now(),
                is_read=False,
            )

# Signal for creating a notification when a new announcement is created
@receiver(post_save, sender=Comment)
def send_event_comment_notification(sender, instance, created, **kwargs):
    if created:
        # Fetch all homeowners with the role 'owner'
        admin_users = User.objects.filter(is_staff=True)

        events_url = reverse('admin_announcements')

        # Create a notification for each admin
        for admin in admin_users:
            message = f"""
                    <a href="{events_url}">
                        {instance.owner_commentor.first_name} commented on the event <span class='font-bold'>'{instance.event.event_name}' \n
                        <span>'{instance.comment}'</span>
                    </a>
                """
            # Create a notification for each homeowner
            AdminNotification.objects.create(
                admin=admin,
                icon="bi-chat-left-text",  # An icon representing a comment, adjust as needed
                message=message,
                created_at=timezone.now(),
                is_read=False,
            )