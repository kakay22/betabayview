from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import ResidentForm
from django.contrib import messages
from USERS.models import HomeOwner, Resident
from USERS.forms import HomeOwnerForm, UserForm, EditUserForm
from .models import Maintenance_request, Activitie, Notification
from ADMIN.models import Event, Comment, Message, Property, Log, PropertyImage, Announcement, AnnouncementComment, PaymentReminder, Feedback
from django.urls import reverse
from django.http import JsonResponse
from google.cloud import dialogflow_v2 as dialogflow
from django.views.decorators.http import require_POST
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import uuid
from google.api_core import exceptions as google_exceptions
from SECRETARY.signals import create_maintenance_request_notification, create_not_verified_notification, create_verified_notification
from HOMEOWNER.signals import notify_max_request
from ADMIN.signals import admin_create_not_verified_notification, admin_create_verified_notification, admin_create_maintenance_request_notification
from django.utils import timezone
from datetime import timedelta
from ADMIN.forms import AnnouncementCommentForm
from USERS.forms import CustomPasswordChangeForm
from django.contrib.auth import update_session_auth_hash

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Update the session with the new password hash
            update_session_auth_hash(request, user)  # Prevents logout
            messages.success(request, 'Your password has been successfully updated!')
            return redirect('owner_dashboard')  # Redirect to success page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'change_password.html', {'form': form})

# Create your views here.
def check_auth_status(request):
    """
    This view returns whether the user is authenticated or not
    """
    return JsonResponse({'authenticated': request.user.is_authenticated})

@login_required
def add_member(request):
    user = request.user
    homeowner = HomeOwner.objects.get(user=user)
    notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')
    profile = homeowner.profile_picture.url

    if request.method == 'POST':
        form = ResidentForm(request.POST)
        if form.is_valid():
            # Populate fields and save form instance
            resident = form.save(commit=False)
            resident.block_number = homeowner.block_number
            resident.house_number = homeowner.house_number
            resident.household_representative = user
            resident.save()

            # Update the total household members for the homeowner
            homeowner.total_household_members = Resident.objects.filter(household_representative=user).count()
            homeowner.save()

            # Log the activity
            new_act = Activitie.objects.create(
                name_of_owner=user,
                name_of_activity='Added a new household member.'
            )
            new_act.save()

            # Log the adition of member //check//
            Log.objects.create(
                log_type='info',
                description=f"Homeowner '{request.user}' added a household member '{resident.first_name}'.",
                user=request.user
            )

            messages.success(request, 'Member added successfully')
            # Send a JSON success response
            return JsonResponse({
                'success': True,
                'message': 'A member is added successfully!',
                'redirect_url': reverse('household_members')  # Reverse URL for redirection
            })
        else:
            # Return form errors as JSON
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)

    else:
        form = ResidentForm()

    return render(request, 'add_member.html', {
        'form': form,
        'profile': profile,
        'user': user,
        'username': user.username,
        'notifications': notifications,
    })

from django.db.models import F
from django.db.models.functions import Lower  # Correct import

@login_required
def household_members(request):
    message = request.GET.get('message', None)
    user = User.objects.get(username=request.user)
    homeowner = HomeOwner.objects.get(user=user)
    notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')
    profile = homeowner.profile_picture.url
    id = user.pk

    # Get sorting criteria from GET parameters (default is by ID, descending)
    sort_option = request.GET.get('sort', 'id_desc')

    # Define sorting logic with case-insensitive sorting for name fields
    if sort_option == 'name_asc':
        sort_by = Lower('first_name')  # Case-insensitive sort for first name (ascending)
    elif sort_option == 'name_desc':
        sort_by = Lower('first_name').desc()  # Case-insensitive sort for first name (descending)
    elif sort_option == 'age_asc':
        sort_by = 'age'
    elif sort_option == 'age_desc':
        sort_by = '-age'
    elif sort_option == 'relationship_to_household_asc':
        sort_by = 'relationship_to_household'
    elif sort_option == 'rrelationship_to_household_desc':
        sort_by = '-relationship_to_household'
    else:
        sort_by = '-pk'  # Default sorting by ID

    # Fetch and order residents based on sorting
    residents = Resident.objects.filter(household_representative=user).all().order_by(sort_by)

    paginator = Paginator(residents, 6)  # Show 6 residents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        return add_member(request)  # Handle form submission

    form = ResidentForm()

    # Pass the current sorting option to the template to persist it
    return render(request, 'household_members.html', {
        'page_obj': page_obj,
        'profile': profile,
        'paginator': paginator,
        'id': id,
        'notifications': notifications,
        'message': message,
        'form': form,
        'current_sort': sort_option  # Pass current sort option
    })


def check_email_existence(request):
    if request.method == 'POST':
        email_address = request.POST.get('email_address')
        exists = Resident.objects.filter(email_address=email_address).exists()
        return JsonResponse({'exists': exists})

def edit_member(request, pk):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_address = request.POST.get('email_address')
        contact_number = request.POST.get('contact_number')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        occupation = request.POST.get('occupation')
        relationship_to_household = request.POST.get('relationship_to_household')

        if first_name and last_name and email_address and contact_number and age and gender and occupation and relationship_to_household:
            member = get_object_or_404(Resident, pk=pk)

            # Check if the email is being changed and exists
            if member.email_address != email_address and Resident.objects.filter(email_address=email_address).exists():
                messages.error(request, 'Email address already exists. Please use a different one.')
                return redirect('edit_member', pk=pk)

            member.first_name = first_name
            member.last_name = last_name
            member.email_address = email_address
            member.contact_number = contact_number
            member.age = age
            member.gender = gender
            member.occupation = occupation
            member.relationship_to_household = relationship_to_household
            member.save()

            # Log the updating of member
            Log.objects.create(
                log_type='info',
                description=f"Homeowner '{request.user}' updated a household member '{member.first_name}'.",
                user=request.user
            )

            messages.info(request, 'Update saved')
            return redirect('household_members')
        else:
            return redirect('household_members')

def delete_member(request, pk):
    if request.method == 'POST':
        member_delete = Resident.objects.get(pk=pk)

        # Log the deleting of member //check//
        Log.objects.create(
            log_type='info',
            description=f"Homeowner '{request.user}' deleted a household member '{member_delete.first_name}'.",  # Adjust field if necessary
            user=request.user
        )

        member_delete.delete()
        messages.info(request, 'member deleted successfully!')
        return redirect('household_members')

def update_picture(request, pk):
    user = User.objects.get(username=request.user)
    homeowner = HomeOwner.objects.get(user=user)
    name_of_owner = user
    if request.method == 'POST' and 'picture' in request.FILES:
        picture = request.FILES['picture']
        user = User.objects.get(pk=pk)

        if picture:
            homeowner.profile_picture = picture
            homeowner.save()

            #to activities
            new_act = Activitie.objects.create(
                    name_of_owner = name_of_owner,
                    name_of_activity = 'Updated profile picture.'
                )
            new_act.save()

            # Log updating of profile //check//
            Log.objects.create(
                log_type='info',
                description=f"Homeowner '{request.user}' updated his profile.",  # Adjust field if necessary
                user=request.user
            )

            messages.info(request, 'Profile saved')
            return redirect('owner_profile')

@login_required
def maintenance_request(request):
    user = get_object_or_404(User, pk=request.user.pk)
    current_date = timezone.now()

    # Get the current date
    current_date = timezone.now()
    current_month = current_date.month
    current_year = current_date.year

    # Count the number of maintenance requests in the current month
    request_count = Maintenance_request.objects.filter(
        name_of_owner=user,
        date_requested__month=current_month,
        date_requested__year=current_year
    ).count()

    if request.method == 'POST':
         # Check if user has reached the maximum number of maintenance requests
        if request_count >= 5:
            messages.error(request, 'You have reached the maximum of 5 requests for this month.')
            notify_max_request(user)
            return redirect('owner_dashboard')

        # Get the posted form data
        description_of_issue = request.POST.get('description_of_issue')
        type_of_issue = request.POST.get('type_of_issue')
        location = request.POST.get('location_of_issue')
        image = request.FILES.get('image')  # Handle the optional file

        # Fetch homeowner and property data
        homeowner = HomeOwner.objects.get(user=user)
        my_property = Property.objects.get(household_head=homeowner)

        if description_of_issue and type_of_issue and location:
            # Create a new maintenance request
            maintenance_req = Maintenance_request.objects.create(
                name_of_owner=user,
                property=my_property,
                Description_of_issue=description_of_issue,
                type_of_issue=type_of_issue,
                location=location,
                image=image if image else None,  # Handle cases where there is no image
            )

            # Save maintenance request
            maintenance_req.save()

            # Log the request
            Log.objects.create(
                log_type='info',
                description=f"Homeowner '{request.user}' requested maintenance: '{maintenance_req.Description_of_issue}' for property '{my_property.property_name}'.",
                user=request.user
            )

            # Add an activity log
            Activitie.objects.create(
                name_of_owner=user,
                name_of_activity='Requested a maintenance.'
            )

            # Send notifications about the request
            create_maintenance_request_notification(maintenance_req)
            admin_create_maintenance_request_notification(maintenance_req)

            # Success message
            messages.success(request, 'Your maintenance request has been submitted.')

            return redirect('request_maintenance_list')

    # For non-POST method, redirect to owner dashboard
    return redirect('owner_dashboard')


def request_verification(request):
    if request.method == 'POST':
        request_pk = request.POST.get('request_pk')
        verification = request.POST.get('verification')
        feedback = request.POST.get('feedback')

        requestMaintenance = get_object_or_404(Maintenance_request, pk=request_pk)
        if verification and feedback:
            requestMaintenance.status=verification
            requestMaintenance.feedback=feedback
            # Check if the status is 'Verified' to set the date_resolved
            if verification == 'verified':
                requestMaintenance.date_resolved = timezone.now()

            requestMaintenance.save()

            # Log verification of request //check//
            Log.objects.create(
                log_type='info',
                description=f"Homeowner '{request.user}' mark the maintenance '{requestMaintenance.Description_of_issue}' as '{requestMaintenance.status}' with a feedback '{requestMaintenance.feedback}'.",  # Adjust field if necessary
                user=request.user
            )

            messages.success(request, 'Verfication submitted')

            if verification == 'notverified':
                create_not_verified_notification(requestMaintenance)
                admin_create_not_verified_notification(requestMaintenance)
            else:
                requestMaintenance.feedback=feedback
                create_verified_notification(requestMaintenance)
                admin_create_verified_notification(requestMaintenance)

            return redirect('owner_notifications')

@login_required
def request_maintenance_list(request):
    # Get the current logged-in user
    user = get_object_or_404(User, username=request.user)

    # Get the Homeowner instance associated with the user
    homeowner = HomeOwner.objects.get(user=user)

    # Fetch notifications related to the user (homeowner)
    notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')

    # Fetch the profile picture if it exists, otherwise set it to None
    profile = homeowner.profile_picture.url if homeowner.profile_picture else None

    # Fetch the current date, month, and year
    current_date = timezone.now()
    current_month = current_date.month
    current_year = current_date.year

    # Determine the filter option from the request, default to 'current' month if not provided
    filter_option = request.GET.get('filter', 'current')

    # Filter maintenance requests based on the selected filter option
    if filter_option == 'previous':
        # Fetch requests from previous months in the current year
        maintenance_requests = Maintenance_request.objects.filter(
            name_of_owner=user,
            date_requested__month__lt=current_month,
            date_requested__year=current_year
        ).order_by('-date_requested')
    else:
        # Fetch requests for the current month
        maintenance_requests = Maintenance_request.objects.filter(
            name_of_owner=user,
            date_requested__month=current_month,
            date_requested__year=current_year
        ).order_by('-date_requested')

    # Paginate the maintenance requests (5 requests per page)
    paginator = Paginator(maintenance_requests, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Count the number of maintenance requests in the current month
    request_count = Maintenance_request.objects.filter(
        name_of_owner=user,
        date_requested__month=current_month,
        date_requested__year=current_year
    ).count()

    # Calculate the percentage usage, ensuring it doesn't exceed 100%
    percentage_used = min((request_count / 5) * 100, 100)

    # Render the request_maintenance_list template with the context
    return render(request, 'request_maintenance_list.html', {
        'page_obj': page_obj,  # Paginated maintenance requests
        'paginator': paginator,  # Paginator instance for page navigation
        'profile': profile,  # Homeowner's profile picture
        'id': user.pk,  # User ID
        'notifications': notifications,  # User's notifications
        'request_count': request_count,  # Number of requests for the current month
        'percentage_used': percentage_used,  # Percentage used of requests
        'filter_option': filter_option  # Filter option for current/previous month
    })

def edit_request(request, pk):
    if request.method == 'POST':
        description = request.POST.get('description')
        type_of_issue = request.POST.get('type_of_issue')
        location = request.POST.get('location')

        if description and type_of_issue and location:
            request_to_edit = Maintenance_request.objects.get(pk=pk)
            request_to_edit.Description_of_issue = description
            request_to_edit.type_of_issue = type_of_issue
            request_to_edit.location = location
            request_to_edit.save()

            # Log updating of request //check//
            Log.objects.create(
                log_type='info',
                description=f"Homeowner '{request.user}' updated the maintenance '{request_to_edit.Description_of_issue}'.",  # Adjust field if necessary
                user=request.user
            )

            messages.info(request, 'Update saved!')
            return redirect('request_maintenance_list')

def delete_request(request, pk):
    if request.method == 'POST':
        request_to_delete = Maintenance_request.objects.get(pk=pk)

        # Log updating of request //check//
        Log.objects.create(
            log_type='info',
            description=f"Homeowner '{request.user}' deleted the maintenance '{request_to_delete.Description_of_issue}'.",  # Adjust field if necessary
            user=request.user
        )

        request_to_delete.delete()
        messages.info(request, 'Deleted successfully!')
        return redirect('request_maintenance_list')

@login_required
def owner_events(request):
    user_name = request.user
    user = User.objects.get(username=user_name)
    homeowner = HomeOwner.objects.get(user=user)
    notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')
    profile = homeowner.profile_picture.url
    id = user.pk
    events = Event.objects.all()
    return render(request, 'owner_events.html', {'user_name':user_name, 'events':events, 'profile':profile, 'id':id, 'notifications':notifications,})

def owner_event_detail(request, pk):
    user = User.objects.get(username=request.user)
    homeowner = HomeOwner.objects.get(user=user)
    notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')
    profile = homeowner.profile_picture.url
    id = user.pk
    event = Event.objects.get(pk=pk)
    comments = Comment.objects.filter(event=event).order_by('-date_commented')
    return render(request, 'owner_event_detail.html', {'event':event, 'profile':profile, 'id':id, 'comments':comments, 'notifications':notifications,})

@login_required
def owner_announcements(request):
    # Fetch all announcements ordered by creation date
    announcements = Announcement.objects.all().order_by('-created_at')
    announcement_comment = AnnouncementComment.objects.all().order_by('-created_at')
    user = User.objects.get(username=request.user)
    homeowner = HomeOwner.objects.get(user=user)
    profile = homeowner.profile_picture.url
    comment_form = AnnouncementCommentForm()
    return render(request, 'owner_announcement.html', {'announcements': announcements, 'announcement_comment':announcement_comment, 'profile':profile, 'comment_form':comment_form})

def owner_announcement_comment(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    owner = get_object_or_404(HomeOwner, user=request.user)
    owner_profile = owner.profile_picture
    if request.method == 'POST':
        comment_form = AnnouncementCommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.announcement = announcement
            new_comment.user = request.user
            new_comment.profile = owner_profile
            new_comment.save()
            messages.success(request, 'Comment submitted')
            return redirect('owner_announcements')
    else:
        comment_form = AnnouncementCommentForm()

def add_owner_comment(request, pk):
    if request.method == 'POST':
        event = Event.objects.get(pk=pk)

        owner_commentor_id = request.POST.get('owner_commentor')
        comment = request.POST.get('comment')

        get_user = User.objects.get(pk=owner_commentor_id)
        homeowner = HomeOwner.objects.get(user=get_user)

        user_image = homeowner.profile_picture

        if owner_commentor_id and comment:
            # Create and save the new comment
            new_comment = Comment.objects.create(
                owner_commentor=get_user,  # Link the User object
                event=event,  # Link the Event object
                comment=comment,  # The actual comment text
                image=user_image  # User's profile picture, assuming it exists in HomeOwner
            )

            # Log the action of the homeowner adding a comment //check//
            Log.objects.create(
                log_type='info',
                description=f"Homeowner '{get_user.username}' commented '{new_comment.comment}' on the event '{event.event_name}'.",
                user=request.user,  # The admin or user who initiated the comment action
            )

            messages.success(request, 'Comment submitted')
            # Redirect to the event detail page after saving the comment
            return redirect(reverse('owner_event_detail', args=[pk]))

    # If the request is not POST, redirect back to the event details page
    return redirect(reverse('owner_event_detail', args=[pk]))


@login_required
def property_selection(request):
    user = User.objects.get(username=request.user)
    homeowner = HomeOwner.objects.get(user=user)
    notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')
    profile = homeowner.profile_picture.url
    id = user.pk
    available_properties = Property.objects.filter(availability='available')
    property_images = PropertyImage.objects.all()
    return render(request, 'property_selection.html', {'profile':profile, 'id':id, 'notifications':notifications, 'available_properties':available_properties, 'property_images':property_images})

@login_required
def confirm_selection(request, pk):
    if request.method == 'POST':
        user = User.objects.get(username=request.user)
        homeowner = HomeOwner.objects.get(user=user)
        selected_property = Property.objects.get(pk=pk)
        selected_property.household_head = homeowner
        selected_property.availability = 'occupied'
        selected_property.save()


        owner = HomeOwner.objects.get(user=user)
        owner.property = selected_property
        owner.save()

        # Log selection of property //check//
        Log.objects.create(
            log_type='info',
            description=f"Homeowner '{request.user}' selected '{selected_property.property_name}' as his property.",  # Adjust field if necessary
            user=request.user
        )

        messages.success(request, 'Property selection done')
        return redirect('property_detail')

@login_required
def property_detail(request):
    user = User.objects.get(username=request.user)
    homeowner = HomeOwner.objects.get(user=user)
    notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')
    profile = homeowner.profile_picture.url
    id = user.pk

    if Property.objects.filter(household_head=homeowner).exists():
        my_property = Property.objects.get(household_head=homeowner)
    else:
        my_property = None

    maintenance_history = Maintenance_request.objects.filter(name_of_owner=user).order_by('-date_requested')

    # Get filter from URL query params
    filter_type = request.GET.get('filter', 'interior')  # 'interior' as default

    # Filter images based on the selected type
    property_images = PropertyImage.objects.filter(property=my_property)

    return render(request, 'property_detail.html', {'profile':profile, 'id':id, 'notifications':notifications, 'my_property':my_property, 'maintenance_history':maintenance_history, 'property_images':property_images, 'filter_type':filter_type})

def get_property_images(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id)
    images = property_instance.images.all().values('id', 'image')

    # Build the image URL for the response
    image_list = [{'id': img['id'], 'url': img['image'].url} for img in images]
    return JsonResponse(image_list, safe=False)


def owner_unread_notifications_count(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(is_read=False, homeowner=request.user).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'unread_count': 0})

@require_POST
def mark_notifications_as_read(request):
    user = request.user
    user = get_object_or_404(User, username=user)
    Notification.objects.filter(homeowner=user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})

def mark_single_notification_as_read(request, notification_id):
    user = request.user
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            notification = Notification.objects.get(pk=notification_id, homeowner=user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'ok'})
        except Notification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

@csrf_exempt
def get_new_messages(request):
    if request.method == 'GET':
        messages = Message.objects.filter(is_read=False).order_by('-sent_time')[:20]  # Adjust to your needs
        messages_list = [{
            'sender': msg.sender,  # Ensure this matches your Message model's sender field
            'message': msg.message,
            'created_at': msg.sent_time.strftime('%Y-%m-%d %H:%M:%S')
        } for msg in messages]
        return JsonResponse(messages_list, safe=False)

@csrf_exempt
def mark_messages_as_read(request):
    if request.method == 'POST':
        Message.objects.filter(is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})

def get_profile_message(sender_username):
    try:
        homeowner = HomeOwner.objects.get(user=sender_username)
        return homeowner.profile_picture.url if homeowner.profile_picture else None
    except HomeOwner.DoesNotExist:
        return None

@login_required
def owner_messages(request):
    user = User.objects.get(username=request.user)
    homeowner = HomeOwner.objects.get(user=user)
    user_name = request.user.username
    notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')
    profile = homeowner.profile_picture.url
    id = user.pk

    messages = Message.objects.all()
    messages_with_pictures = []

    for message in messages:
        profile_picture_url = get_profile_message(request.user)
        messages_with_pictures.append({
            'message': message,
            'profile_picture_url': profile_picture_url,
        })

    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            new_message = Message.objects.create(
                sender=user_name,
                message=message,
            )
            new_message.save()
            return redirect('owner_messages')

    return render(request, 'owner_messages.html', {'profile':profile, 'id':id, 'notifications':notifications, 'messages_with_pictures':messages_with_pictures})

from django.contrib.auth import login

def owner_profile(request):
    message = request.GET.get('message', None)
    user = User.objects.get(username=request.user)
    homeowner = HomeOwner.objects.get(user=user)
    notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')
    profile = homeowner.profile_picture.url

    if Property.objects.filter(household_head=homeowner).exists():
        my_property = Property.objects.get(household_head=homeowner)
    else:
        my_property = 'None'

    id = user.pk

    if request.method == 'POST':
        userForm = EditUserForm(request.POST, instance=user)
        ownerForm = HomeOwnerForm(request.POST, request.FILES, instance=homeowner)

        # Debugging: Print form errors
        if userForm.is_valid() and ownerForm.is_valid():
            # Save the user form (this will update the email and username)
            user = userForm.save(commit=False)

            # If you're changing username or email, it's important to commit these changes before session update
            user.save()

            # Now, save the owner form
            ownerForm.save()

            # Prevent logout by updating the session with the new user credentials
            # Re-authenticate the user after saving the changes
            login(request, user)  # Log the user back in


            # Log the profile update
            Log.objects.create(
                log_type='info',
                description=f"Homeowner '{request.user.username}' updated their profile information.",
                user=request.user
            )

            # Notify the user of the successful update
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('owner_profile')
        else:
            messages.error(request, 'Please correct errors below')
            print("User Form Errors: ", userForm.errors)
            print("Owner Form Errors: ", ownerForm.errors)
    else:
        userForm = EditUserForm(instance=user)
        ownerForm = HomeOwnerForm(instance=homeowner)

    return render(request, 'owner_profile.html', {
        'profile': profile,
        'id': id,
        'notifications': notifications,
        'homeowner': homeowner,
        'my_property': my_property,
        'userForm': userForm,
        'ownerForm': ownerForm,
        'message': message,
    })


def owner_notifications(request):
    message = request.GET.get('message', None)
    user = User.objects.get(username=request.user)
    homeowner = HomeOwner.objects.get(user=user)
    notifications = Notification.objects.filter(homeowner=request.user).order_by('-created_at')
    profile = homeowner.profile_picture.url

    return render(request, 'owner_notifications.html', {
        'profile': profile,
        'id': id,
        'notifications': notifications,
        'homeowner': homeowner,
        'message': message,
    })

def owner_delete_all_notif(request, pk):
    owner = User.objects.get(pk=pk)
    if request.method == 'POST':
        del_notif = Notification.objects.filter(homeowner=owner)
        del_notif.delete()
        return redirect('owner_notifications')


def chatbot(request):
    return render(request, 'chatbot.html')

def detect_intent(request):
    # Retrieve the query parameter from the request
    text = request.GET.get('query', '')
    print(f"Received query: {text}")  # Debugging

    # Check if the session ID exists in the session data, else generate a new one
    if 'session_id' not in request.session:
        request.session['session_id'] = str(uuid.uuid4())

    # Retrieve session ID
    session_id = request.session['session_id']
    print(f"Session ID: {session_id}")  # Debugging

    # Initialize Dialogflow session client
    try:
        session_client = dialogflow.SessionsClient()
    except Exception as e:
        print(f"Failed to create a Dialogflow session client: {e}")
        return JsonResponse({'response': 'Failed to connect to Dialogflow service.'})

    # Create session path
    session = session_client.session_path('dynamic-cooler-434604-i2', session_id)

    # Prepare the text input for the query
    text_input = dialogflow.TextInput(text=text, language_code='en')
    query_input = dialogflow.QueryInput(text=text_input)

    try:
        # Send the detect intent request to Dialogflow
        response = session_client.detect_intent(request={"session": session, "query_input": query_input})
        print(f"Dialogflow response: {response.query_result.fulfillment_text}")
    except google_exceptions.PermissionDenied as e:
        print(f"Permission Denied: {e}")
        print("Check if the service account has the required IAM permissions.")
        return JsonResponse({'response': 'Permission denied. Please check your permissions and try again.'})
    except google_exceptions.GoogleAPIError as e:  # Catch other Google API errors
        print(f"Google API Error: {e}")
        return JsonResponse({'response': 'An error occurred with the Google API. Please try again later.'})
    except Exception as e:
        print(f"Error: {e}")  # General error
        import traceback
        traceback.print_exc()  # Print the full error stack trace
        return JsonResponse({'response': 'Sorry, something went wrong.'})

    # Return the response from Dialogflow
    return JsonResponse({'response': response.query_result.fulfillment_text})

import openai
# from openai import error
import logging
import time
from django.http import JsonResponse
from django.shortcuts import render

# Set up OpenAI API Key
# openai.api_key = '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'  # Replace with your OpenAI API key


# def chatbot2(request):
#     if request.method == 'POST':
#         user_input = request.POST.get('message')
#         max_retries = 5  # Set the maximum number of retries
#         wait_time = 1  # Start with a 1-second wait

#         for attempt in range(max_retries):
#             try:
#                 # Use the new ChatCompletion API
#                 response = openai.ChatCompletion.create(
#                     model="gpt-3.5-turbo",
#                     messages=[
#                         {"role": "system", "content": "You are a helpful assistant."},
#                         {"role": "user", "content": user_input}
#                     ]
#                 )
#                 chatbot_response = response['choices'][0]['message']['content'].strip()
#                 return JsonResponse({'response': chatbot_response})

#             except error.AuthenticationError:
#                 logging.error("Invalid API key.")
#                 return JsonResponse({'response': "Invalid API key. Please check your configuration."})

#             except error.RateLimitError:
#                 logging.warning(f"Rate limit exceeded. Attempt {attempt + 1} of {max_retries}.")
#                 if attempt < max_retries - 1:  # If not the last attempt
#                     wait_time_message = f"Rate limit exceeded. Please wait {wait_time} seconds before trying again."
#                     print(wait_time)
#                     time.sleep(wait_time)  # Wait before retrying
#                     wait_time *= 2  # Exponentially increase the wait time
#                     return JsonResponse({'response': wait_time_message})
#                 else:
#                     return JsonResponse({'response': "Rate limit exceeded. Please try again later."})

#             except error.APIConnectionError:
#                 logging.error("Failed to connect to OpenAI API.")
#                 return JsonResponse({'response': "Failed to connect to OpenAI API. Please check your internet connection."})

#             except error.OpenAIError as e:
#                 logging.error(f"OpenAI error: {e}")
#                 return JsonResponse({'response': f"An error occurred: {str(e)}"})

#             except Exception as e:
#                 logging.error(f"Unexpected error: {e}")
#                 return JsonResponse({'response': f"An error occurred: {str(e)}"})

#     return render(request, 'chatbot2.html')


def payment_reminder(request, pk):
    owner = get_object_or_404(User, pk=request.user.pk)
    reminder = PaymentReminder.objects.get(pk=pk)
    homeowner = HomeOwner.objects.get(user=owner)
    profile = homeowner.profile_picture.url
    return render(request, 'payment_reminder.html', {'reminder':reminder,'owner':owner, 'profile':profile})

def chat(request):
    return render(request, 'chat.html')

def submit_feedback(request):
    if request.method == 'POST':
        feedback_type = request.POST['feedbackType']
        subject = request.POST['feedbackSubject']
        description = request.POST['feedbackDescription']
        contact_info = request.POST.get('feedbackContact', '')

        # Save the feedback
        feedback = Feedback(
            user=request.user if request.user.is_authenticated else None,
            feedback_type=feedback_type,
            subject=subject,
            description=description,
            contact_info=contact_info
        )
        feedback.save()

        messages.success(request, 'Thank you for your feedback!')
        return redirect('owner_dashboard')  # Replace with your desired redirect URL

#for visit request notification
def notification_details(request, notif_id):
    try:
        notification = Notification.objects.get(pk=notif_id)
        visit_request = notification.visit_request  # assuming you have this relation
        return JsonResponse({
            'visitor_full_name': visit_request.visitor_full_name,
            'visitor_relation': visit_request.visitor_relation,
            'visit_date': visit_request.visit_date.strftime('%Y-%m-%d %H:%M'),
            'purpose': visit_request.purpose
        })
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)
