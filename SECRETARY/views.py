from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from USERS.models import HomeOwner, Resident
from ADMIN.models import Secretary, Event, Comment, Property, Message, MaintenancePersonnel, Log, PropertyImage, Announcement, AnnouncementComment, PaymentReminder, PropertyModel
from USERS.forms import HomeOwnerForm, UserForm
from ADMIN.forms import SecretaryForm, EditOwnerForm, PropertyForm, EventForm, RepairmanForm, AnnouncementForm, AnnouncementCommentForm
from SECRETARY.forms import ResidentForm
from django.contrib import messages
from HOMEOWNER.models import Maintenance_request, Notification
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string
from .models import SecNotification
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

# Create your views here.
def check_auth_status(request):
    """
    This view returns whether the user is authenticated or not
    """
    return JsonResponse({'authenticated': request.user.is_authenticated})

@login_required
def secretary_dashboard(request):
    message = request.GET.get('message', None)
    totalHomeowners = HomeOwner.objects.filter(pending=False).count
    totalPendings = HomeOwner.objects.filter(pending=True).count
    maintenances = Maintenance_request.objects.order_by('-date_requested')[:5]
    events = Event.objects.all().order_by('-date_created')[:3]
    totalProperties = Property.objects.all().count
    occupied_properties = Property.objects.filter(availability='occupied')
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url

    return render(request, 'secretary_dashboard.html', {'totalPendings':totalPendings, 'maintenances':maintenances, 'events':events, 'totalProperties':totalProperties, 'totalHomeowners':totalHomeowners, 'occupied_properties':occupied_properties, 'profile':profile, 'message':message})


# @login_required
# def sec_homeowners(request):
#     message = request.GET.get('message', None)

#     selected_property = request.GET.get('houseFilter', '')  # Get the selected filter option

#     if selected_property != "":
#         selected_property = get_object_or_404(Property, property_name=selected_property)
#         homeowners = HomeOwner.objects.filter(pending=False, property=selected_property)
#     else:
#         homeowners = HomeOwner.objects.filter(pending=False).all().order_by('-registration_date')

#     form = UserForm()

#     homeowners = HomeOwner.objects.filter(pending=False).all()
#     paginator = Paginator(homeowners, 6)  # Show 6 requests per page
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     houses = Property.objects.all()

#     secretary = Secretary.objects.get(user=request.user)
#     profile = secretary.profile_picture.url

#     return render(request, 'sec_homeowners.html', {
#         'form': form,
#         'homeowners': homeowners,
#         'message': message,
#         'page_obj': page_obj,
#         'profile': profile,
#         'houses':houses,
#     })

@login_required
def sec_homeowners(request):
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    message = request.GET.get('message', None)
    selected_property = request.GET.get('houseFilter', '')  # Get the selected filter option
    selected_block = request.GET.get('blockFilter', '')  # Get the selected filter option
    has_property = request.GET.get('hasProperty', '')  # Check if homeowner has a property or not
    sort_by = request.GET.get('sort', '')  # Get the selected sort option

    # Initialize the queryset for homeowners
    homeowners_list = HomeOwner.objects.filter(pending=False)

    # Apply filters based on selected options
    if selected_property:
        selected_property = get_object_or_404(Property, property_name=selected_property)
        homeowners = homeowners_list.filter(property=selected_property)
    elif selected_block:
        homeowners = homeowners_list.filter(property__property_block_no=selected_block)
    elif has_property == "yes":
        homeowners = homeowners_list.filter(property__isnull=False)  # Homeowners with a property
    elif has_property == "no":
        homeowners = homeowners_list.filter(property__isnull=True)  # Homeowners without a property
    else:
        homeowners = homeowners_list  # All homeowners if no filter is applied

    # Apply sorting
    if sort_by == "name":
        homeowners = homeowners.order_by('user__first_name')  # Sort by name
    elif sort_by == "registration_date":
        homeowners = homeowners.order_by('-registration_date')  # Sort by registration date
    else:
        homeowners = homeowners.order_by('-registration_date')  # Default sorting

    paginator = Paginator(homeowners, 6)  # Show 6 requests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    houses = Property.objects.all()

    if request.method == 'POST':
        form = UserForm(request.POST)

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        if first_name == '':
            form.add_error('first_name', 'This field is required.')
        if last_name == '':   
            form.add_error('last_name', 'This field is required.')
        if email == '':
            form.add_error('email', 'This field is required.')
        else:
            if form.is_valid():
                user = form.save()
                homeowner = HomeOwner.objects.create(
                    user=user,
                    pending=False,
                )
                
                homeowner.save()
                messages.success(request, 'Homeowner created successfully')
                return redirect('sec_homeowners')
    else:
        form = UserForm()

    return render(request, 'sec_homeowners.html', {
        'homeowners': homeowners,
        'message': message,
        'page_obj': page_obj,
        'paginator': paginator,
        'form': form,
        'houses': houses,
        'profile': profile,
        'selected_block': selected_block,
        'has_property': has_property,
        'sort_by': sort_by,  # Pass the sort option to the template
    })


def sec_owner_profile(request, pk):
    owner = HomeOwner.objects.get(pk=pk)

    try:
        owner_property = Property.objects.get(household_head=owner.pk)
    except ObjectDoesNotExist:
        owner_property = None
    
    total_household_members = Resident.objects.filter(household_representative=owner.user).count
    owner_maintenances = Maintenance_request.objects.filter(name_of_owner=owner.user.pk)

    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    return render(request, 'sec_owner_profile.html', {'owner':owner, 'owner_property':owner_property, 'total_household_members':total_household_members, 'owner_maintenances':owner_maintenances, 'profile':profile})

def sec_payment_reminder(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        owner_name = user.first_name
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        property_owned = request.POST.get('property')
        owner = get_object_or_404(HomeOwner, user=user)

        # Create the PaymentReminder
        payment_reminder = PaymentReminder.objects.create(
            homeowner=owner,
            amount=amount,
            due_date=due_date,
            sender=request.user
        )
        payment_reminder.save()

        # Generate the URL to the payment reminder page
        payment_reminder_url = reverse('payment_reminder', kwargs={'pk': payment_reminder.pk})
        mess = f"""
                <a href="{payment_reminder_url}">
                    Reminder for your payment of your property at Beta Bayview Homes. Click to view details
                </a>
                """

        # Create the notification
        notification = Notification.objects.create(
            homeowner=user,
            icon='bi-bell-fill',  # Customize icon as needed
            message= mess,
            is_read=False,
            created_at=timezone.now(),
            notif_url = payment_reminder_url,
            maintenance_request=None  # Can be null if not related to maintenance
        )
        notification.save()

        # Log the payment reminder action
        Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user}' sent a payment reminder to '{owner_name} {user.last_name}'.",
            user=request.user
        )

        # Display success message
        messages.success(request, 'Payment reminder sent successfully.')

        owner_pk = request.POST.get('owner_pk')
        # Redirect to sec_owner_profile page with the correct pk
        return redirect(reverse('sec_owner_profile', kwargs={'pk': owner_pk}))

    else:
        # If not a POST request, simply redirect to the owner's profile
        return redirect(reverse('sec_owner_profile', kwargs={'pk': pk}))

@login_required
def sec_homeowner_detail(request, pk):
    owner = HomeOwner.objects.get(pk=pk)
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    household_members = Resident.objects.filter(household_representative=owner.user)

    if Property.objects.filter(household_head=owner).exists():
        property_details = Property.objects.get(household_head=owner)
    else:
        property_details = 'none'

    maintenances = Maintenance_request.objects.filter(name_of_owner=owner.user)
    return render(request, 'sec_homeowner_detail.html', {'owner':owner, 'household_members':household_members, 'property_details':property_details, 'maintenances':maintenances, 'profile':profile})


@login_required
def sec_maintenance_request_list(request):
    # Retrieve query parameters for filtering and sorting
    status_filter = request.GET.get('status', 'all')  # Default to 'all'
    sort_by = request.GET.get('sort', 'date_requested')  # Default to sorting by date_requested

    # Base queryset
    total_maintenance_req = Maintenance_request.objects.all()

    # Apply status filtering
    if status_filter != 'all':
        total_maintenance_req = total_maintenance_req.filter(status=status_filter)

    # Apply sorting
    total_maintenance_req = total_maintenance_req.order_by(f'-{sort_by}', 'id')  # Allows sorting by date_resolved as well

    # Pagination
    paginator = Paginator(total_maintenance_req, per_page=10)  # Set per_page to 10
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    return render(request, 'sec_maintenance_request_list.html', {'page_obj': page_obj, 'profile':profile, 'status_filter':status_filter})

@login_required
def sec_maintenance_personnel_list(request):
    personnel = MaintenancePersonnel.objects.all()
    requests = Maintenance_request.objects.all()
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url

    if request.method == 'POST':
        return sec_add_repairman(request)  # Handle form submission

    form = RepairmanForm()
    return render(request, 'sec_maintenance_personnel.html', {'personnel':personnel, 'requests':requests, 'form':form, 'profile':profile})

def sec_delete_all_repairman(request):
    if request.method == 'POST':
        personnels = MaintenancePersonnel.objects.all()
        personnels.delete()

        # Log creation for deletion of all repairman //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user}' deleted all repairman.",
            user=request.user,
        )

        messages.info(request, 'All Repairman has been deleted')
        return redirect('sec_maintenance_personnel_list')

def sec_add_repairman(request):
    if request.method == 'POST':
        form = RepairmanForm(request.POST, request.FILES)
        if form.is_valid():
            repairman = form.save()  # Save the new repairman to the database
            messages.success(request, 'Repairman successfully added')

            # Create a log entry for adding new repairman //check//
            Log.objects.create(
                log_type='success',  # Adjust log type as necessary
                description=f"Secretary '{request.user.username}' added a repairman: '{repairman.name}-{repairman.role}'",  # Replace 'name' with the actual field for repairman name
                user=request.user  # Assuming you have a user field in your Log model
            )

            return JsonResponse({
                'success': True,
                'message': 'Repairman successfully added!'  # Success message
            })
        else:
            print(form.errors)  # Debugging - Log form errors
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })  # Return validation errors

    return JsonResponse({'success': False, 'message': 'Invalid request'})

def sec_edit_personnel(request, pk):
    personnel = get_object_or_404(MaintenancePersonnel, pk=pk)
    
    if request.method == 'POST':
        # Store old data for logging purposes (optional)
        old_data = {
            'name': personnel.name,
            'role': personnel.role,
            'status': personnel.status,
            'phone': personnel.phone,
            'email': personnel.email,
            'location': personnel.location,
        }

        # Update personnel with new data
        personnel.name = request.POST.get('name')
        personnel.role = request.POST.get('role')
        personnel.status = request.POST.get('status')
        personnel.phone = request.POST.get('phone')
        personnel.email = request.POST.get('email')
        personnel.location = request.POST.get('location')
        personnel.save()

        # Create a log entry
        Log.objects.create(
            log_type='info',  # or 'success'
            description=f"Secretary '{request.user}' updated personnel '{personnel.name}'.",
            user=request.user,
            action=f"Old data: {old_data} -> New data: {request.POST}"  # Optional: log old vs new data
        )

        messages.success(request, 'Personnel details updated successfully!')
        return redirect('sec_maintenance_personnel_list')  # Replace with your actual redirect route

def sec_delete_personnel(request, pk):
    personnel = get_object_or_404(MaintenancePersonnel, pk=pk)
    
    if request.method == 'POST':
        personnel_name = personnel.name  # Store name for logging before deletion
        personnel.delete()

        # Create a log entry
        Log.objects.create(
            log_type='warning',  # or 'info' depending on how you classify deletions
            description=f"Secretary '{request.user}' deleted personnel '{personnel_name}'.",
            user=request.user,
            action=f"Deleted personnel '{personnel_name}'"
        )

        messages.success(request, 'Personnel deleted successfully!')
        return redirect('sec_maintenance_personnel_list')  # Replace with your actual redirect route

def sec_assign_request(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        person_id = request.POST.get('person_id')
        personel_name = request.POST.get('personel_name')
        
        # Get the request and personnel objects
        maintenance_request = get_object_or_404(Maintenance_request, pk=request_id)
        repair_personnel = get_object_or_404(MaintenancePersonnel, pk=person_id)
        
        # Update request and personnel statuses
        maintenance_request.status = 'In progress'
        maintenance_request.repairman = personel_name
        maintenance_request.save()

        # Log creation for setting status in progress //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user.username}' set the status 'In progress' for '{maintenance_request.Description_of_issue}' request from '{maintenance_request.name_of_owner.first_name}'.",
            user=request.user,
        )
        log.save()

        # Log creation for assigning repairman to a request maintenance //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user.username}' assigned repairman '{repair_personnel.name}' for '{maintenance_request.Description_of_issue}' request from '{maintenance_request.name_of_owner.first_name}'.",
            user=request.user,
        )
        log.save()
        
        repair_personnel.status = 'Ongoing maintenance'
        repair_personnel.save()
        
        messages.success(request, 'Repairman assigned')
        return redirect('sec_maintenance_personnel_list')  # Replace with your actual redirect URL
    else:
        messages.error(request, 'Invalid request.')
        return redirect('sec_maintenance_personnel_list')  # Replace with your actual redirect URL

import logging

@login_required
def sec_residents(request):
    message = request.GET.get('message', None)
    search_query = request.GET.get('search', '')
    household_representative_query = request.GET.get('household_representative', '')  
    sort_by = request.GET.get('sort', 'first_name')  # Default sort by first name

    residents = Resident.objects.all()

    # Filtering by search query
    if search_query:
        residents = residents.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )

    # Filtering by household representative if specified
    if household_representative_query:
        residents = residents.filter(household_representative__username=household_representative_query)

    # Sorting residents
    if sort_by in ['first_name', 'last_name', 'created_at']:
        residents = residents.order_by(sort_by)

    paginator = Paginator(residents, 5)  # Show 5 residents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url

    # Prepare a list of homeowners for the dropdown
    homeowners = HomeOwner.objects.filter(user__isnull=False)
    household_representatives = [(homeowner.user.username, homeowner.user.first_name) for homeowner in homeowners]

    if request.method == 'POST':
        form = ResidentForm(request.POST)
        if form.is_valid():
            resident = form.save()
            log = Log.objects.create(
                log_type='info',
                description=f"Secretary '{request.user.username}' created resident: '{resident.first_name}'.",
                user=request.user,
            )
            log.save()
            messages.success(request, 'Resident added successfully')
    else:
        form = ResidentForm()

    return render(request, 'sec_residents.html', {
        'message': message,
        'page_obj': page_obj,
        'profile': profile,
        'form': form,
        'household_representatives': household_representatives,
        'search_query': search_query,
        'sort_by': sort_by,
        'household_representative': household_representative_query,  # Pass the selected representative
    })

@login_required
def sec_new_resident(request):

    if request.method == 'POST':
        form = ResidentForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new resident

            # Log creation
            log = Log.objects.create(
                log_type='info',
                description=f"Secretary '{request.user.username}' created resident: '{form.first_name}'.",
                user=request.user,
            )
            log.save()

            return JsonResponse({'success': True})
        else:
            # Return the form with errors as HTML
            form_html = render_to_string('sec_residents.html', {'form': form})
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        form = ResidentForm()

def sec_edit_resident(request, pk):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_address = request.POST.get('email_address')
        contact_number = request.POST.get('contact_number')
        occupation = request.POST.get('occupation')

        if first_name and last_name and email_address and contact_number and occupation:
            resident = Resident.objects.get(pk=pk)
            resident.first_name=first_name
            resident.last_name=last_name
            resident.contact_number=contact_number
            resident.email_address=email_address
            resident.occupation=occupation
            resident.save()

            # Log creation for update resident //check//
            log = Log.objects.create(
                log_type='info',
                description=f"Secretary '{request.user.username}' updated resident: '{resident.first_name}'.",
                user=request.user,
            )
            log.save()

            messages.info(request, 'Update saved!')
            return redirect('sec_residents')
    
def sec_delete_resident(request, pk):
     if request.method == 'POST':
        resident_to_delete = Resident.objects.get(pk=pk)

        # Log creation for deleting resident //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user.username}' deleted resident: '{resident_to_delete.first_name}'.",
            user=request.user,
        )
        log.save()

        resident_to_delete.delete()
        messages.info(request, 'Deleted successfully!')
        return redirect('sec_residents')
          

@login_required
def sec_pending_accounts(request):
    message = request.GET.get('message')
    pendings = HomeOwner.objects.filter(pending=True)
    paginator = Paginator(pendings, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    return render(request, 'sec_pending.html', {'pendings':pendings, 'page_obj':page_obj, 'message':message, 'profile':profile})

def get_pending_registrations(request):
    if request.method == 'GET':
        count = HomeOwner.objects.filter(pending=True).count()  # Adjust query according to your model
        return JsonResponse({'count': count})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def mark_messages_as_read(request):
    if request.method == 'POST':
        # Perform your logic to mark messages as read
        HomeOwner.objects.filter(pending=True).update(status='read')
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def sec_messages(request):
	return render(request, 'sec_messages.html')

def sec_acceptPending(request, pk):
    pendingAccount = get_object_or_404(HomeOwner, pk=pk)
    pendingAccount.pending = False
    account_email = pendingAccount.user.email
    account_firstname = pendingAccount.user.first_name
    pendingAccount.save()

    sec_send_account_accepted_email(account_email, account_firstname)
    messages.success(request, 'Owner account accepted!')
    return redirect('sec_pending_accounts')

def sec_send_account_accepted_email(homeowner_email, firstname):
    subject = 'BAYVIEW HOMES - Housing Management System'
    message = f"Hello {firstname}, Your account has been accepted. You can now log in and manage your household ."
    from_email = settings.DEFAULT_FROM_EMAIL
    recepient_list = [homeowner_email]

    send_mail(subject, message, from_email, recepient_list)

def sec_deny_pending(request, pk):
    pendingAccount = get_object_or_404(HomeOwner, pk=pk)

    # Log creation for denying pending //check//
    log = Log.objects.create(
        log_type='info',
        description=f"Secretary '{request.user.username}' denied pending account for '{pendingAccount.user.first_name}'.",
        user=request.user,
    )
    log.save()

    user = pendingAccount.user
    pendingAccount.delete()

    if user:
        user.delete()

    messages.info(request, 'Account denied')
    return redirect('sec_pending_accounts')

@login_required
def sec_new_homeowner(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            homeowner = HomeOwner.objects.create(
                user=user,
                pending=False,
            )
            homeowner.save()

            # Log creation //check//
            log = Log.objects.create(
                log_type='info',
                description=f"Secretary {request.user.username} created a new homeowner: {homeowner.user.username}",
                user=request.user
            )
            log.save()
            
            # Check if the request is AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Homeowner created successfully!'})
            else:
                return redirect('sec_homeowners')
        else:
            errors = form.errors.as_json()  # Get errors as JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': errors})
            else:
                # For non-AJAX requests, return the form with errors
                return render(request, 'sec_homeowners.html', {'form': form, 'errors': errors})
    else:
        form = UserForm()
    
    return render(request, 'sec_homeowner.html', {'form': form})

def sec_delete_owner(request, pk):
    if request.method == 'POST':
        # Retrieve the HomeOwner object
        homeowner = get_object_or_404(HomeOwner, pk=pk)
        
        # Retrieve the associated User object
        user = homeowner.user

        # Log creation for deleting homeowner //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user.username}' deleted homeowner: '{homeowner.user.first_name}'.",
            user=request.user,
        )
        log.save()
        
        # Delete the HomeOwner object
        homeowner.delete()
        
        # Delete the associated User object
        if user:
            user.delete()
        
        # Redirect with a success message
        messages.info(request, 'Deleted successfully')
        return redirect('sec_homeowners')

def sec_edit_owner(request, pk):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        contact_number = request.POST.get('contact_number')
        email_address = request.POST.get('email_address')
        occupation = request.POST.get('occupation')

        if first_name and last_name and contact_number and email_address and occupation:
            owner = get_object_or_404(HomeOwner, pk=pk)
            user = owner.user
            user.first_name = first_name
            user.last_name = last_name
            owner.contact_number = contact_number
            user.email = email_address
            owner.occupation = occupation
            user.save()
            owner.save()

            # Log creation for updating owner //check//
            log = Log.objects.create(
                log_type='info',
                description=f"Secretary '{request.user.username}' updated homeowner: '{user.first_name}'.",
                user=request.user,
            )
            log.save()

            messages.success(request, 'Update saved!')
            return redirect('sec_homeowners')
        else:
            messages.error(request, 'Theres a problem submitting your form')
            return redirect('sec_homeowners')
    else:
        messages.error(request, 'Submit failed')
        return redirect('sec_homeowners')

from django.db.models import Q

def sec_get_maintenances(request):
    if request.method == 'GET':
        count = Maintenance_request.objects.filter(Q(status='Pending') | Q(status='notverified')).count()  # Adjust query according to your model
        return JsonResponse({'count': count})
    return JsonResponse({'error': 'Invalid request'}, status=400)

# def sec_change_to_onGoing(request, pk):
#     if request.method == 'POST':
#         req = get_object_or_404(Maintenance_request, pk=pk)
#         req.status = 'On going'
#         req.save()
#         return redirect('sec_maintenance_request_list')

def sec_change_to_done(request, pk):
    if request.method == 'POST':
        req = get_object_or_404(Maintenance_request, pk=pk)
        req.status = 'Done'
        req.save()

        # Get the homeowner's email through the connected User model
        homeowner = req.name_of_owner  # Assuming `name_of_owner` is linked to `HomeOwner`
        homeowner_name = homeowner.first_name  # Assuming `HomeOwner` has a `name` field
        homeowner_email = homeowner.email  # Assuming `HomeOwner` has a link to `User` model with email

        # Send email to the homeowner
        subject = 'Maintenance Request Completed'
        message = f"Hello {homeowner_name}, your maintenance request '{req.Description_of_issue}' has been marked as completed. Please log in to verify the completion."
        from_email = settings.DEFAULT_FROM_EMAIL

        #change status of repairman to available
        repairman_name = req.repairman
        assigned_repairman = MaintenancePersonnel.objects.get(name=repairman_name)
        assigned_repairman.status = 'available'
        assigned_repairman.save()

        # Log creation change to done //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user.username}' set the status 'Done' for '{req.Description_of_issue}' request from '{homeowner_name}'.",
            user=request.user,
        )
        log.save()

        try:
            send_mail(
                subject,
                message,
                from_email,
                [homeowner_email],
                fail_silently=False,
            )
            messages.info(request, "Maintenance request marked as done.")
        except Exception as e:
            messages.error(request, f"Request marked as done, but email failed to send: {e}")

        return redirect('sec_maintenance_request_list')

@login_required
def sec_events(request):
    message = request.GET.get('message', None)
    events = Event.objects.all().order_by('-date_created')
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            # Log creation for creating event //check//
            log = Log.objects.create(
                log_type='info',
                description=f"Secretary '{request.user.username}' created an event : '{event.event_name}' .",
                user=request.user,
            )
            log.save()
            messages.success(request, 'Event created successfully!')
            return redirect('sec_events')
    else:
        form = EventForm()

    return render(request, 'sec_events.html', {'events':events, 'form':form, 'profile':profile, 'message':message})

@login_required
def sec_announcements(request):
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    # Fetch all announcements ordered by creation date
    announcements = Announcement.objects.all().order_by('-created_at')
    announcement_comment = AnnouncementComment.objects.all().order_by('-created_at')
    comment_form = AnnouncementCommentForm()

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)  # Create the Announcement instance but don’t save it yet
            announcement.created_by = request.user  # Set the user who created the announcement
            
            # Check if the user has a profile picture; otherwise, set the default
            if hasattr(request.user, 'profile_picture'):
                announcement.profile_picture = request.user.userprofile.profile_picture
            else:
                announcement.profile_picture = 'admin.png'  # Fallback default image
            
            announcement.save()  # Save the announcement to the database

            # Log creation for creating annoucement //check//
            log = Log.objects.create(
                log_type='info',
                description=f"Secretary '{request.user.username}' created an annoucement : '{announcement.title}' .",
                user=request.user,
            )
            log.save()

            messages.success(request, 'Announcement created successfully.')  # Success message
            return redirect('sec_announcements')  # Redirect to the announcements page
    else:
        form = AnnouncementForm()  # Create an empty form for GET requests

    return render(request, 'sec_announcement.html', {'announcements': announcements, 'form': form, 'announcement_comment':announcement_comment, 'profile':profile, 'comment_form':comment_form})

def sec_edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        announcement.title = title
        announcement.content = content

         # Log creation for creating annoucement //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user.username}' updated an annoucement : '{announcement}' .",
            user=request.user,
        )
        log.save()

        announcement.save()

        messages.info(request, 'update saved!')
        return redirect('sec_announcements')

def sec_delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)

    if request.method == 'POST':
        announcement.delete()

        # Log creation for creating annoucement //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user.username}' deleted an annoucement : '{announcement.title}' .",
            user=request.user,
        )
        log.save()

        announcement.save()

        messages.info(request, 'deleted success!')
        return redirect('sec_announcements')

def sec_announcement_comment(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    secretary = get_object_or_404(Secretary, user=request.user)
    owner_profile = secretary.profile_picture
    if request.method == 'POST':
        comment_form = AnnouncementCommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.announcement = announcement
            new_comment.user = request.user
            new_comment.profile = owner_profile
            new_comment.save()
            messages.success(request, 'Comment submitted')
            return redirect('sec_announcements')
    else:
        comment_form = AnnouncementCommentForm()

def sec_maintenance_requests_data(request):
    # Aggregate requests created per month
    requests_per_month = (
        Maintenance_request.objects
        .annotate(month=TruncMonth('date_requested'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Aggregate issues by type and month
    issue_type_per_month = (
        Maintenance_request.objects
        .annotate(month=TruncMonth('date_requested'))
        .values('month', 'type_of_issue')
        .annotate(count=Count('id'))
        .order_by('month', 'type_of_issue')
    )

    return JsonResponse({
        'requests_per_month': list(requests_per_month),
        'issue_type_per_month': list(issue_type_per_month)
    })

@login_required
def sec_event_detail(request, pk):
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    event = Event.objects.get(pk=pk)
    comments = Comment.objects.filter(event=event).order_by('-date_commented')
    return render(request, 'sec_event_detail.html', {'event':event, 'comments':comments, 'profile':profile})

def sec_edit_event(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        event_name = request.POST.get('event_name')
        event_description = request.POST.get('event_description')
        event_date = request.POST.get('event_date')
        event_time = request.POST.get('event_time')

        event.event_name=event_name
        event.event_description=event_description
        event.event_date=event_date
        event.event_time=event_time

        if 'image' in request.FILES:
            event.image=request.FILES('image')
        else:
            event.image=event.image

        event.save()

        # Log creation for updating event //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user.username}' updated the event : '{event.event_name}' .",
            user=request.user,
        )
        log.save()

        messages.success(request, 'Event update saved!')
        return redirect('sec_events')

def sec_delete_event(request, pk):
    if request.method == 'POST':
        del_event = Event.objects.get(pk=pk)

         # Log creation for deleting event //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user.username}' deleted the event : '{del_event.event_name}' .",
            user=request.user,
        )
        log.save()

        del_event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('sec_events')

# def sec_add_owner_comment(request, pk):
#     if request.method == 'POST':
#         event = Event.objects.get(pk=pk)
#         owner_commenter = request.POST.get('owner_commentor')
#         event_name = event.event_name
#         comment = request.POST.get('comment')

#         if owner_commenter and comment:
#             new_comment = Comment.objects.create(
#                 owner_commenter=owner_commenter,
#                 event=event_name,
#                 comment=comment,
#             )
#             new_comment.save()
#             return redirect(reverse('sec_event_detail', args=[pk]))

@login_required
def sec_properties(request):
    message = request.GET.get('message', None)
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    
    # Filter logic for availability and block
    availability_filter = request.GET.get('availability')
    block_filter = request.GET.get('block')
    model_filter = request.GET.get('property_model')

    properties = Property.objects.all()
    property_models = PropertyModel.objects.all()

    if availability_filter:
        properties = properties.filter(availability=availability_filter)

    if block_filter:
        properties = properties.filter(property_block_no=block_filter)
    
    # Filter by model
    if model_filter:
        properties = properties.filter(property_model=model_filter)  # Adjust according to your model field name

    property_images = PropertyImage.objects.all()


    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            new_property = form.save(commit=False)
            new_property.property_model = form.cleaned_data['property_model']  # Set the property model
            new_property.save()  # Save the new property to the database
            messages.success(request, 'Property added successfully!')
            
            Log.objects.create(
                log_type='info',
                description=f"Secretary '{request.user}' added a new property: '{new_property.property_name}'.",  
                user=request.user
            )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Property added successfully!'})
            
            return redirect('/sec_properties/?message=Property added successfully!')
        else:
            errors = form.errors.as_json()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': errors})
    else:
        form = PropertyForm()

    return render(request, 'sec_properties.html', {
        'properties': properties,
        'message': message,
        'form': form,
        'profile': profile,
        'property_images': property_images,
        'availability_filter': availability_filter,
        'block_filter': block_filter,
        'property_models':property_models,
        'model_filter':model_filter
    })

def sec_property_detail(request, pk):
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    owner_property = Property.objects.get(pk=pk)

    # Get filter from URL query params
    filter_type = request.GET.get('filter', 'interior')  # 'interior' as default

    # Filter images based on the selected type
    property_images = PropertyImage.objects.filter(property=owner_property)

    try:
        owner = HomeOwner.objects.get(property=owner_property)
        owner_maintenances = Maintenance_request.objects.filter(name_of_owner=owner.user.pk)
    except ObjectDoesNotExist:
        owner = None  # Or handle as needed
        owner_maintenances = None

    if request.method == 'POST':
        if 'new_interior_image' in request.FILES:
            # Handle interior image upload
            new_image = PropertyImage(property=owner_property, interrior_image=request.FILES['new_interior_image'])
            new_image.save()
            messages.success(request, 'Interior image uploaded successfully.')
        elif 'new_exterior_image' in request.FILES:
            # Handle exterior image upload
            new_image = PropertyImage(property=owner_property, exterrior_image=request.FILES['new_exterior_image'])
            new_image.save()
            messages.success(request, 'Exterior image uploaded successfully.')
        redirect(reverse('sec_property_detail', kwargs={'pk': owner_property.id}))

    return render(request, 'sec_property_detail.html', {'owner_property':owner_property, 'property_images':property_images, 'maintenances':owner_maintenances,'filter_type':filter_type, 'profile':profile})


@login_required
def upload_property_images(request, pk):
    if request.method == 'POST':
        images = request.FILES.getlist('images')

        uploaded_images = []

        property_instance = get_object_or_404(Property, pk=pk)

        for img in images:
            property_image = PropertyImage.objects.create(
                property=property_instance,
                image=img,
            )
            uploaded_images.append({
                'url': property_image.image.url,  # Assuming you have an image field in your model
            })

        # Check the uploaded_images list
        print(uploaded_images)  # Debugging line to ensure images are being processed

        return JsonResponse({'success': True, 'images': uploaded_images})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

def get_property_images(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id)
    images = property_instance.images.all().values('id', 'image')
    
    # Build the image URL for the response
    image_list = [{'id': img['id'], 'url': img['image'].url} for img in images]
    return JsonResponse(image_list, safe=False)

@login_required
def sec_edit_property(request, pk):
    if request.method == 'POST':
        property_name = request.POST.get('property_name')
        block_number = request.POST.get('block_no')
        house_number = request.POST.get('lot_no')
        property_description = request.POST.get('property_description')
        
        if block_number and house_number:
            prop = Property.objects.get(pk=pk)
            prop.property_name = property_name
            prop.property_block_no = block_number
            prop.property_house_no = house_number
            prop.property_description = property_description
            prop.save()

            # Log the update property //check//
            Log.objects.create(
                log_type='info',
                description=f"Secretary '{request.user}' updated the property '{prop.property_name}'.",  
                user=request.user
            )

            messages.success(request, 'Property update saved!')
            return redirect('sec_properties')

def sec_delete_property(request, pk):
    if request.method == 'POST':
        del_property = Property.objects.get(pk=pk)

        # Log the deletion of all properties //check//
        Log.objects.create(
            log_type='info',
            description=f"Secretary '{request.user}' deleted all properties'.",  
            user=request.user
        )

        del_property.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('sec_properties')

@csrf_exempt
def sec_get_new_messages(request):
    if request.method == 'GET':
        messages = Message.objects.all().order_by('-sent_time')[:20]  # Adjust to your needs
        messages_list = [{
            'sender': msg.sender,  # Adjust the field based on your model
            'message': msg.message,
            'created_at': msg.sent_time
        } for msg in messages]
        return JsonResponse(messages_list, safe=False)

def get_profile_message(sender_username):
    try:
        user = User.objects.get(username=sender_username)
        homeowner = HomeOwner.objects.get(user=user)
        return homeowner.profile_picture.url if homeowner.profile_picture else None
    except HomeOwner.DoesNotExist:
        return None

@login_required
def sec_messages(request):
    messages = Message.objects.all()
    secretary = Secretary.objects.get(user=request.user)
    profile = secretary.profile_picture.url
    messages_with_pictures = []

    for message in messages:
        profile_picture_url = get_profile_message(message.sender)
        messages_with_pictures.append({
            'message': message,
            'profile_picture_url': profile_picture_url,
        })

    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            new_message = Message.objects.create(
                sender=request.user.username,
                message=message
            )
            new_message.save()
            return redirect('sec_messages')

    return render(request, 'sec_messages.html', {'messages_with_pictures':messages_with_pictures, 'profile':profile})

# @login_required
# def sec_add_property(request):
#     message = request.GET.get('message', None)
#     secretary = Secretary.objects.get(user=request.user)
#     profile = secretary.profile_picture.url
#     if request.method == 'POST':
#         form = PropertyForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Property added successfully!')
#             return redirect('sec_properties')
#     else:
#         form = PropertyForm()
#     return render(request, 'sec_add_property.html', {'form':form, 'profile':profile, 'message':message})

@login_required
def sec_notifications(request):
    message = request.GET.get('message', None)
    user = User.objects.get(username=request.user)
    secretary = Secretary.objects.get(user=user)
    notifications = SecNotification.objects.all().order_by('-created_at')
    profile = secretary.profile_picture.url

    return render(request, 'sec_notifications.html', {
        'profile': profile,
        'id': id,
        'notifications': notifications,
        'secretary': secretary,
        'message': message,
    })

def unread_notifications_count(request):
    if request.user.is_authenticated:
        unread_count = SecNotification.objects.filter(is_read=False).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'unread_count': 0})

@require_POST
def sec_mark_notifications_as_read(request):
    user = request.user
    SecNotification.objects.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})

@require_POST
def sec_mark_single_notification_as_read(request, notification_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            notification = SecNotification.objects.get(pk=notification_id)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'ok'})
        except SecNotification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

import json

@csrf_exempt
def sec_post_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message')
        sender = data.get('sender')

        if message and sender:
            Message.objects.create(message=message, sender=sender)
            return JsonResponse({'status': 'success'}, status=200)
    return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

def sec_get_new_messages(request):
    last_message_id = request.GET.get('last_message_id', 0)
    messages = Message.objects.filter(id__gt=last_message_id).order_by('sent_time')
    message_list = [
        {
            'id': msg.id,
            'message': msg.message,
            'sender': msg.sender,
            'sent_time': msg.sent_time,
        } for msg in messages
    ]
    return JsonResponse({'messages': message_list})


def sec_live_chat(request):    
    user = User.objects.get(username=request.user)
    secretary = Secretary.objects.get(user=user)
    profile = secretary.profile_picture.url
    return render(request, 'sec_live_chat.html', {'profile':profile})

@login_required
def sec_get_unread_messages_count(request):
    unread_count = Message.objects.filter(
        is_read=False
    ).exclude(sender=request.user.username).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def sec_mark_all_messages_as_read(request):
    # Mark all messages sent to the current user as read
    Message.objects.filter(
        is_read=False
    ).exclude(sender=request.user.username).update(is_read=True)
    return JsonResponse({'status': 'success'})