from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from USERS.models import HomeOwner, Resident
from .models import Secretary, Event, Comment, Property, Message, MaintenancePersonnel, AdminNotification, Log, PropertyImage, Announcement, AnnouncementComment, PaymentReminder, ChatFeedback, ChatHistoryMessage
from USERS.forms import HomeOwnerForm, UserForm
from HOMEOWNER.forms import ResidentForm
from .forms import SecretaryForm, EditOwnerForm, PropertyForm, EventForm, RepairmanForm, AnnouncementForm, AnnouncementCommentForm
from django.contrib import messages
from HOMEOWNER.models import Maintenance_request, Notification, Activitie
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count
from django.utils.timezone import now
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string
from SECRETARY.models import SecNotification
from django.views.decorators.http import require_POST
from .signals import admin_create_maintenance_request_notification
from SECRETARY.signals import create_maintenance_request_notification


# Create your views here.
def check_auth_status(request):
    """
    This view returns whether the user is authenticated or not
    """
    return JsonResponse({'authenticated': request.user.is_authenticated})

@login_required
def admin_dashboard(request):
    totalHomeowners = HomeOwner.objects.filter(pending=False).count
    totalPendings = HomeOwner.objects.filter(pending=True).count
    maintenances = Maintenance_request.objects.order_by('-date_requested')[:5]
    events = Event.objects.all().order_by('-date_created')[:3]
    totalProperties = Property.objects.all().count
    occupied_properties = Property.objects.filter(availability='occupied')
    return render(request, 'admin_dashboard.html', {'totalPendings':totalPendings, 'maintenances':maintenances, 'events':events, 'totalProperties':totalProperties, 'totalHomeowners':totalHomeowners, 'occupied_properties':occupied_properties})

def maintenance_requests_data(request):
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

def get_events(request):
    events = Event.objects.all().values('title', 'start_date')  # Adjust fields as needed
    event_list = list(events)  # Convert QuerySet to list
    return JsonResponse(event_list, safe=False)

@login_required
def homeowners(request):
    message = request.GET.get('message', None)
    selected_property = request.GET.get('houseFilter', '')
    selected_block = request.GET.get('blockFilter', '')
    has_property = request.GET.get('hasProperty', '')
    sort_by = request.GET.get('sort', '')  # Get the selected sort option

    # Initialize the queryset for homeowners
    homeowners_list = HomeOwner.objects.filter(pending=False)

    # Apply filters based on selected options
    if selected_property:
        selected_property = get_object_or_404(Property, property_name=selected_property)
        homeowners_list = homeowners_list.filter(property=selected_property)
    elif selected_block:
        homeowners_list = homeowners_list.filter(property__property_block_no=selected_block)
    elif has_property == "yes":
        homeowners_list = homeowners_list.filter(property__isnull=False)  # Homeowners with a property
    elif has_property == "no":
        homeowners_list = homeowners_list.filter(property__isnull=True)  # Homeowners without a property

    # Apply sorting
    if sort_by == "name":
        homeowners_list = homeowners_list.order_by('user__first_name')  # Sort by name (assuming the first name is part of the User model)
    elif sort_by == "registration_date":
        homeowners_list = homeowners_list.order_by('-registration_date')  # Sort by registration date

    paginator = Paginator(homeowners_list, 6)  # Show 6 requests per page
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

    return render(request, 'homeowners.html', {
        'homeowners': homeowners_list,
        'message': message,
        'page_obj': page_obj,
        'paginator': paginator,
        'form': form,
        'houses': houses,
        'selected_block': selected_block,
        'has_property': has_property,
        'sort_by': sort_by,  # Pass the sort option to the template if needed
    })


# def filter_properties(request):
#     selected_property = request.GET.get('houseFilter', '')  # Get the selected filter option

#     # Fetch all properties for the dropdown
#     all_properties = Property.objects.all()

#     # Filter based on selected property, if any
#     if selected_property:
#         properties = Property.objects.filter(property_name__icontains=selected_property)
#     else:
#         properties = all_properties

#     return render(request, 'homeowners.html', {
#         'properties': properties,  # Filtered properties for the table
#         'all_properties': all_properties,  # All properties for the dropdown
#         'selected_property': selected_property,  # Preserve selected property in the template
#     })


def admin_owner_profile(request, pk):
    owner = HomeOwner.objects.get(pk=pk)
    total_household_members = Resident.objects.filter(household_representative=owner.user).count
    owner_maintenances = Maintenance_request.objects.filter(name_of_owner=owner.user.pk)
    return render(request, 'admin_owner_profile.html', {'owner':owner,'total_household_members':total_household_members, 'owner_maintenances':owner_maintenances})

def delete_all_homeowners(request):
    if request.method == 'POST':
        homeowners = HomeOwner.objects.all()  # Get all homeowner
        
        # Loop through each homeowner and delete the associated user
        for owner in homeowners:
            if owner.user:  # Check if the homeowner is linked to a user
                owner.user.delete()  # Delete the associated user
        
        # Now delete all secretaries
        homeowners.delete()

        # Log creation
        log = Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user.username}' deleted all the homeowners.",
            user=request.user,
        )
        log.save()

        return redirect('homeowners')  # Redirect to your desired page

@login_required
def maintenance_request_list(request):
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

    return render(request, 'maintenance_request_list.html', {'page_obj': page_obj})



@login_required
def secretaries(request):
    message = request.GET.get('message', None)
    Secretaries = Secretary.objects.all()
    paginator = Paginator(Secretaries, 5)  # Show 5 requests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        form = SecretaryForm(request.POST)
        if form.is_valid():
            # Check if email or username already exists
            email_address = form.cleaned_data['email_address']
            user_name = form.cleaned_data['user_name']
            password = form.cleaned_data['password']

            if Secretary.objects.filter(email_address=email_address).exists():
                form.add_error('email_address', 'This email is already taken.')
            elif Secretary.objects.filter(user_name=user_name).exists():
                form.add_error('user_name', 'This username is already taken.')
            else:
                user = User.objects.create_user(
                    username = user_name,
                    email = email_address,
                    password = password,
                )
                user.save()
                secretary = form.save(commit=False)
                secretary.user = user
                secretary.save()
                messages.success(request, 'New secretary added')

                # Log creation
                log = Log.objects.create(
                    log_type='info',
                    description=f"Admin '{request.user.username}' created secretary account for '{secretary.user.username}'.",
                    user=request.user,
                )
                log.save()
                
                return redirect('secretaries')
    else:
        form = SecretaryForm()

    return render(request, 'secretaries.html', {'message':message, 'page_obj':page_obj, 'Secretaries':Secretaries, 'form':form})

@login_required
def residents(request):
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

    # Prepare a list of homeowners for the dropdown
    homeowners = HomeOwner.objects.filter(user__isnull=False)
    household_representatives = [(homeowner.user.username, homeowner.user.first_name) for homeowner in homeowners]

    if request.method == 'POST':
        form = ResidentForm(request.POST)
        if form.is_valid():
            resident = form.save()
            log = Log.objects.create(
                log_type='info',
                description=f"Admin '{request.user.username}' created resident: '{resident.first_name}'.",
                user=request.user,
            )
            log.save()
            messages.success(request, 'Resident added successfully')
    else:
        form = ResidentForm()

    return render(request, 'residents.html', {
        'message': message,
        'page_obj': page_obj,
        'form': form,
        'household_representatives': household_representatives,
        'search_query': search_query,
        'sort_by': sort_by,
        'household_representative': household_representative_query,  # Pass the selected representative
    })

def delete_resident(request, pk):
     if request.method == 'POST':
        resident_to_delete = Resident.objects.get(pk=pk)

        # Log creation for deleting resident //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user.username}' deleted resident: '{resident_to_delete.first_name}'.",
            user=request.user,
        )
        log.save()

        resident_to_delete.delete()
        messages.info(request, 'Deleted successfully!')
        return redirect('residents')

def edit_resident(request, pk):
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

            messages.info(request, 'Update saved')
            return redirect('residents')

@login_required
def new_resident(request):
    mess = ''
    if request.method == 'POST':
        form = ResidentForm(request.POST)
        if form.is_valid():
            form.save()
            mess = 'Resident added successfully!'
    else:
        form = ResidentForm()
    return render(request, 'new_resident.html', {'form':form, 'mess':mess})

@login_required
def pending_accounts(request):
    message = request.GET.get('message')
    pendings = HomeOwner.objects.filter(pending=True)
    paginator = Paginator(pendings, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'pending_accounts.html', {'pendings':pendings, 'page_obj':page_obj, 'message':message})


def admin_messages(request):
	return render(request, 'messages.html')

def admin_get_pending_registrations(request):
    if request.method == 'GET':
        count = HomeOwner.objects.filter(pending=True).count()  # Adjust query according to your model
        return JsonResponse({'count': count})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def admin_mark_messages_as_read(request):
    if request.method == 'POST':
        # Perform your logic to mark messages as read
        HomeOwner.objects.filter(pending=True).update(status='read')
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def acceptPending(request, pk):
    pendingAccount = get_object_or_404(HomeOwner, pk=pk)
    pendingAccount.pending = False
    account_email = pendingAccount.user.email
    account_firstname = pendingAccount.user.first_name
    pendingAccount.save()

    # Log creation
    log = Log.objects.create(
        log_type='success',
        description=f"Admin '{request.user.username}' accepted pending account for '{pendingAccount.user.first_name}'.",
        user=request.user,
    )
    log.save()

    send_account_accepted_email(account_email, account_firstname)
    messages.success(request, 'Account accepted')
    return redirect('pending_accounts')


def send_account_accepted_email(homeowner_email, firstname):
    subject = 'Housing Management System'
    message = f"Hello {firstname}, Your account has been accepted. You can now log in and manage your household."
    from_email = settings.DEFAULT_FROM_EMAIL
    recepient_list = [homeowner_email]

    send_mail(subject, message, from_email, recepient_list)

@login_required
def deny_pending(request, pk):
    pendingAccount = get_object_or_404(HomeOwner, pk=pk)

    # Log creation
    log = Log.objects.create(
        log_type='info',
        description=f"Admin '{request.user.username}' denied pending account for '{pendingAccount.user.first_name}'.",
        user=request.user,
    )
    log.save()

    # Delete the user first to avoid losing access to the User instance
    userPending = pendingAccount.user
    if userPending:
        userPending.delete()

    # Now delete the pending homeowner account
    pendingAccount.delete()

    messages.info(request, 'Account denied')
    return redirect('pending_accounts')

@login_required
@csrf_exempt
def new_secretary(request):
    if request.method == 'POST':
        form = SecretaryForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['user_name']
            email = form.cleaned_data['email_address']

            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'errors': {'user_name': ['Username already exists.']}}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'errors': {'email_address': ['Email already exists.']}}, status=400)

            # Create User and Secretary if validation passes
            try:
                user = User.objects.create_user(username=username, password=form.cleaned_data['password'], email=email)
                Secretary.objects.create(
                    user=user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    date_of_birth=form.cleaned_data['date_of_birth'],
                    age=form.cleaned_data['age'],
                    gender=form.cleaned_data['gender'],
                    contact_number=form.cleaned_data['contact_number'],
                    name_of_emergency_contact=form.cleaned_data['name_of_emergency_contact'],
                    relationship_to_secretary=form.cleaned_data['relationship_to_secretary'],
                    emergency_contact_number=form.cleaned_data['emergency_contact_number'],
                    highest_educational_attainment=form.cleaned_data['highest_educational_attainment']
                )
                messages.success(request, 'Created successfully!')
                return JsonResponse({'success': True, 'message': 'Created successfully!'})
            except IntegrityError:
                return JsonResponse({'success': False, 'errors': {'non_field_errors': ['Failed to create secretary. Try again.']}}, status=500)
        else:
            # Return form errors
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return render(request, 'add_secretary.html', {'form': SecretaryForm()})

def delete_all_secretaries(request):
    if request.method == 'POST':
        secretaries = Secretary.objects.all()  # Get all secretaries
        
        # Loop through each secretary and delete the associated user
        for secretary in secretaries:
            if secretary.user:  # Check if the secretary is linked to a user
                secretary.user.delete()  # Delete the associated user
        
        # Now delete all secretaries
        secretaries.delete()
        messages.info(request, 'All secretaries deleted successfully!')
        return redirect('secretaries')  # Redirect to your desired page

@login_required
def new_homeowner(request):
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
                description=f"Admin {request.user.username} created a new homeowner: {homeowner.user.username}",
                user=request.user
            )
            log.save()
            
            # Check if the request is AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Homeowner created successfully!'})
            else:
                return redirect('/homeowners/?message=Homeowner%20created%20successfully!')
        else:
            errors = form.errors.as_json()  # Get errors as JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': errors})
            else:
                # For non-AJAX requests, return the form with errors
                return render(request, 'add_homeowner.html', {'form': form, 'errors': errors})
    else:
        form = UserForm()
    
    return render(request, 'add_homeowner.html', {'form': form})

def delete_owner(request, pk):
    if request.method == 'POST':
        # Retrieve the HomeOwner object
        homeowner = get_object_or_404(HomeOwner, pk=pk)
        
        # Retrieve the associated User object
        user = homeowner.user

        # Log creation //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user.username}' deleted homeowner: '{homeowner.user.first_name}'.",
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
        return redirect('homeowners')

def edit_owner(request, pk):
    homeowner = get_object_or_404(HomeOwner, pk=pk)
    user = homeowner.user

    if request.method == 'POST':
        # Get data from the form submission
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        contact_number = request.POST.get('contact_number')
        email_address = request.POST.get('email')
        occupation = request.POST.get('occupation')

        # Validate that all required fields are present
        if first_name and last_name and age and gender and contact_number and email_address and occupation:
            # Update the User model fields
            user.first_name = first_name
            user.last_name = last_name
            user.email = email_address
            user.save()

            # Update the HomeOwner model fields
            homeowner.age = age
            homeowner.gender = gender
            homeowner.contact_number = contact_number
            homeowner.occupation = occupation
            homeowner.save()
            messages.info(request, 'Update saved')

            # Log creation //check//
            log = Log.objects.create(
                log_type='info',
                description=f"Admin '{request.user.username}' updated homeowner: '{homeowner.user.first_name}'.",
                user=request.user,
            )
            log.save()
            return redirect('homeowners')
        else:
            messages.error(request, 'All fields are required')

    # Render the edit form with current data if GET request
    return render(request, 'edit_owner.html', {
        'homeowner': homeowner,
        'user': user
    })

def delete_secretary(request, pk):
    # Retrieve the secretary using the primary key
    secretary = get_object_or_404(Secretary, pk=pk)
    
    # Get the associated user before deleting the secretary
    user = secretary.user  # Assuming Secretary has a OneToOneField or ForeignKey to User

    # Log creation //check//
    log = Log.objects.create(
        log_type='info',
        description=f"Admin '{request.user.username}' deleted secretary: '{secretary.user.username}'.",
        user=request.user,
    )
    log.save()
    
    # Delete the secretary first
    secretary.delete()
    
    # Now delete the associated user
    if user:
        user.delete()
    
    # Redirect to the secretaries page with a success message
    messages.info(request, 'Deleted successfully')
    return redirect('secretaries')

def edit_secretary(request, pk):
    secretary = Secretary.objects.get(pk=pk)
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        contact_number = request.POST.get('contact_number')
        email_address = request.POST.get('email_address')
        user_name = request.POST.get('user_name')

        if first_name and last_name and contact_number and email_address and user_name:
            secretary.first_name = first_name
            secretary.last_name = last_name
            secretary.contact_number = contact_number
            secretary.email_address = email_address
            secretary.user_name = user_name
            secretary.save()

            # Log creation //check//
            log = Log.objects.create(
                log_type='info',
                description=f"Admin '{request.user.username}' updated secretary: '{secretary.user.username}'.",
                user=request.user,
            )
            log.save()

            messages.info(request, 'Update saved!')
            return redirect('secretaries')

# @login_required
# def maintenance_request_list(request):
#     total_maintenance_req = Maintenance_request.objects.all()
#     paginator = Paginator(total_maintenance_req, 5)  # Show 10 requests per page

#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     return render(request, 'maintenance_request_list.html', {'page_obj': page_obj})

# def change_to_onGoing(request, pk):
#     if request.method == 'POST':
#         req = get_object_or_404(Maintenance_request, pk=pk)
#         req.status = 'In progress'
#         req.save()

#         # Log creation
#         log = Log.objects.create(
#             log_type='info',
#             description=f"Admin '{request.user.username}' set the status 'In progress' for '{req.Description_of_issue}'.",
#             user=request.user,
#         )
#         log.save()
        
#         return redirect('maintenance_request_list')

def change_to_done(request, pk):
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

        # Log creation //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user.username}' set the status 'Done' for '{req.Description_of_issue}' request from '{homeowner_name}'.",
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
            messages.info(request, "Maintenance request marked as done")
        except Exception as e:
            messages.error(request, f"Request marked as done, but email failed to send: {e}")

        return redirect('maintenance_request_list')

@login_required
def admin_maintenance_personnel_list(request):
    personnel = MaintenancePersonnel.objects.all()
    requests = Maintenance_request.objects.all()

    if request.method == 'POST':
        return admin_add_repairman(request)  # Handle form submission
    

    form = RepairmanForm()
    return render(request, 'admin_maintenance_personnel.html', {'personnel':personnel, 'requests':requests, 'form':form})

def admin_delete_all_repairman(request):
    if request.method == 'POST':
        personnels = MaintenancePersonnel.objects.all()
        personnels.delete()

        # Log creation for deletion of all repairman //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user.username}' deleted all repairman.",
            user=request.user,
        )
        log.save()

        messages.info(request, 'All Repairman has been deleted')
        return redirect('admin_maintenance_personnel_list')

def admin_add_repairman(request):
    if request.method == 'POST':
        form = RepairmanForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract the name and role from the form
            repairman_name = form.cleaned_data['name']  # Adjust field name as necessary
            repairman_role = form.cleaned_data['role']  # Adjust field name as necessary
            
            # Check for existing names
            existing_repairmen = MaintenancePersonnel.objects.filter(name=repairman_name)
            if existing_repairmen.exists():
                # Create a new name with (2) or increment if already taken
                counter = 2
                new_name = f"{repairman_name} ({counter})"
                while MaintenancePersonnel.objects.filter(name=new_name).exists():
                    counter += 1
                    new_name = f"{repairman_name} ({counter})"
                repairman_name = new_name  # Update the name to the new unique name

            # Check if the maximum number of repairmen for the given role is reached
            role_count = MaintenancePersonnel.objects.filter(role=repairman_role).count()
            if role_count >= 3:
                return JsonResponse({
                    'success': False,
                    'errors': {'role': 'Maximum limit of 3 repairmen for this role has been reached.'}
                })  # Return error if limit is reached

            # Create the repairman instance
            repairman = form.save(commit=False)  # Save the form without committing to the DB yet
            repairman.name = repairman_name  # Set the unique name
            repairman.save()  # Now save the instance

            # Create a log entry
            Log.objects.create(
                log_type='success',  # Adjust log type as necessary
                description=f"Admin '{request.user.username}' added a repairman: '{repairman.name} - {repairman.role}'",
                user=request.user  # Assuming you have a user field in your Log model
            )

            messages.success(request, 'Repairman successfully added')
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



def assign_request(request):
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
            description=f"Admin '{request.user.username}' set the status 'In progress' for '{maintenance_request.Description_of_issue}' request from '{maintenance_request.name_of_owner.first_name}'.",
            user=request.user,
        )
        log.save()

        # Log creation for assigning repairman to a request maintenance //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user.username}' assigned repairman '{repair_personnel.name}' for '{maintenance_request.Description_of_issue}' request from '{maintenance_request.name_of_owner.first_name}'.",
            user=request.user,
        )
        log.save()
        
        repair_personnel.status = 'Ongoing maintenance'
        repair_personnel.save()
        
        messages.success(request, 'Repairman assigned')
        return redirect('admin_maintenance_personnel_list') 
    else:
        messages.error(request, 'Invalid request.')
        return redirect('admin_maintenance_personnel_list') 

@login_required
def events(request):
    events = Event.objects.all().order_by('-event_date')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()

            # Log creation for creating event //check//
            log = Log.objects.create(
                log_type='info',
                description=f"Admin '{request.user.username}' created an event : '{event.event_name}' .",
                user=request.user,
            )
            log.save()

            messages.success(request, 'Event created successfully')
            return redirect('events')
    else:
        form = EventForm()

    return render(request, 'events.html', {'events':events, 'form':form})

@login_required
def admin_announcements(request):
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
            messages.success(request, 'Announcement created successfully.')  # Success message
            return redirect('admin_announcements')  # Redirect to the announcements page
    else:
        form = AnnouncementForm()  # Create an empty form for GET requests

    return render(request, 'admin_announcement.html', {'announcements': announcements, 'form': form, 'announcement_comment':announcement_comment, 'comment_form':comment_form})

def admin_edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        announcement.title = title
        announcement.content = content

         # Log creation for creating annoucement //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user.username}' updated an annoucement : '{announcement}' .",
            user=request.user,
        )
        log.save()

        announcement.save()

        messages.info(request, 'update saved!')
        return redirect('admin_announcements')

def admin_delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)

    if request.method == 'POST':
        announcement.delete()

        # Log creation for creating annoucement //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user.username}' deleted an annoucement : '{announcement.title}' .",
            user=request.user,
        )
        log.save()

        announcement.save()

        messages.info(request, 'deleted success!')
        return redirect('admin_announcements')

def admin_announcement_comment(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        comment_form = AnnouncementCommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.announcement = announcement
            new_comment.user = request.user
            new_comment.profile = None
            new_comment.save()
            messages.success(request, 'Comment submitted')
            return redirect('admin_announcements')
    else:
        comment_form = AnnouncementCommentForm()

@login_required
def event_detail(request, pk):
    event = Event.objects.get(pk=pk)
    comments = Comment.objects.filter(event=event).order_by('-date_commented')
    return render(request, 'event_detail.html', {'event':event, 'comments':comments})

def edit_event(request, pk):
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
            description=f"Admin '{request.user.username}' updated the event : '{event.event_name}' .",
            user=request.user,
        )
        log.save()

        messages.success(request, 'Update saved')
        return redirect('events')

def delete_event(request, pk):
    if request.method == 'POST':
        del_event = Event.objects.get(pk=pk)

        # Log creation for deleting event //check//
        log = Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user.username}' deleted the event : '{del_event.event_name}' .",
            user=request.user,
        )
        log.save()

        del_event.delete()
        messages.info(request, 'Event deleted')
        return redirect('events')

# def add_owner_comment(request, pk):
#     if request.method == 'POST':
#         # Get the event object using the primary key (pk)
#         event = Event.objects.get(pk=pk)
#         owner_commentor = request.POST.get('owner_commentor') 
#         comment = request.POST.get('comment')

#         if owner_commentor and comment:
#             # Create and save the new comment
#             new_comment = Comment.objects.create(
#                 owner_commentor=owner_commentor,
#                 event=event,  # Associate the actual Event object here, not just the name
#                 comment=comment,
#             )
#             new_comment.save()

#             return redirect(reverse('owner_event_detail', args=[pk]))

#     return redirect(reverse('owner_event_detail', args=[pk]))


@login_required
def properties(request):
    # Filter logic for availability and block
    availability_filter = request.GET.get('availability')
    block_filter = request.GET.get('block')

    properties = Property.objects.all()

    if availability_filter:
        properties = properties.filter(availability=availability_filter)

    if block_filter:
        properties = properties.filter(property_block_no=block_filter)

    property_images = PropertyImage.objects.all()

    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            new_property = form.save()
            messages.success(request, 'Property added successfully!')
            
            Log.objects.create(
                log_type='info',
                description=f"Admin '{request.user}' added a new property: '{new_property.property_name}'.",  
                user=request.user
            )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Property added successfully!'})
            
            return redirect('/properties/?message=Property added successfully!')
        else:
            errors = form.errors.as_json()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': errors})
    else:
        form = PropertyForm()

    return render(request, 'properties.html', {
        'properties': properties,
        'form': form,
        'property_images': property_images,
        'availability_filter': availability_filter,
        'block_filter': block_filter
    })

def admin_property_detail(request, pk):
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
        redirect(reverse('admin_property_detail', kwargs={'pk': owner_property.id}))

    return render(request, 'admin_property_detail.html', {'owner_property':owner_property, 'property_images':property_images, 'maintenances':owner_maintenances,'filter_type':filter_type})

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
                'url': property_image.image.url,  # Return the image URL to the frontend
            })

        return JsonResponse({'success': True, 'images': uploaded_images})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


def get_property_images(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id)
    images = property_instance.images.all().values('id', 'image')

    # Build the image URL for the response
    image_list = [{'id': img['id'], 'url': img['image']} for img in images]
    return JsonResponse(image_list, safe=False)



def delete_all_properties(request):
    if request.method == 'POST':
        properties = Property.objects.all()

        # Log the deletion of all properties //check//
        Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user}' deleted all properties'.",  
            user=request.user
        )

        properties.delete()

        messages.info(request, 'All properties deleted')

        return redirect('properties')

@login_required
def edit_property(request, pk):
    if request.method == 'POST':
        property_name = request.POST.get('property_name')
        block_number = request.POST.get('block_no')
        house_number = request.POST.get('lot_no')
        bedroom = request.POST.get('bedroom')
        bathroom = request.POST.get('bathroom')
        property_description = request.POST.get('property_description')
        
        if block_number and house_number:
            prop = Property.objects.get(pk=pk)
            prop.property_name = property_name
            prop.property_block_no = block_number
            prop.property_house_no = house_number
            prop.bedroom = bedroom
            prop.bathroom = bathroom
            prop.property_description = property_description
            prop.save()

            # Log the update property //check//
            Log.objects.create(
                log_type='info',
                description=f"Admin '{request.user}' updated the property '{prop.property_name}'.",  
                user=request.user
            )

            messages.info(request, 'Property update successfully')
            return redirect('properties')

@login_required
def delete_property(request, pk):
    if request.method == 'POST':
        del_property = get_object_or_404(Property, pk=pk)

        # Log the deletion of the property //check//
        Log.objects.create(
            log_type='info',
            description=f"Admin '{request.user}' deleted the property '{del_property.property_name}'.",  # Adjust field if necessary
            user=request.user
        )

        property_images = PropertyImage.objects.filter(property=del_property)
        property_images.delete()

        del_property.delete()

        messages.info(request, 'Property deleted successfully')
        return redirect('properties')

@csrf_exempt
def admin_get_new_messages(request):
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
def admin_messages(request):
    messages = Message.objects.all()
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
            return redirect('admin_messages')

    return render(request, 'admin_messages.html', {'messages_with_pictures':messages_with_pictures,})

# def add_property(request):
#     message = request.GET.get('message', None)
#     if request.method == 'POST':
#         form = PropertyForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Property added successfully!')
#             return redirect('properties')
#     else:
#         form = PropertyForm()
#     return render(request, 'add_property.html', {'form':form, 'message':message})

@require_POST
def mark_notifications_as_read(request):
    user = request.user
    AdminNotification.objects.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})

def admin_unread_notifications_count(request):
    if request.user.is_authenticated:
        unread_count = AdminNotification.objects.filter(is_read=False).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'unread_count': 0})

def admin_mark_single_notification_as_read(request, notification_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            notification = AdminNotification.objects.get(pk=notification_id)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'ok'})
        except AdminNotification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

@login_required
def admin_notifications(request):
    message = request.GET.get('message', None)
    notifications = AdminNotification.objects.all().order_by('-created_at')

    return render(request, 'admin_notifications.html', {
        'notifications': notifications,
        'message': message,
    })

@login_required
def admin_logs(request):
    logs = Log.objects.all().order_by('-timestamp')
    return render(request, 'admin_logs.html', {'logs':logs})

def admin_payment_reminder(request, pk):
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
            description=f"Admin '{request.user}' sent a payment reminder to '{owner_name} {user.last_name}'.",
            user=request.user
        )

        # Display success message
        messages.success(request, 'Payment reminder sent successfully.')

        owner_pk = request.POST.get('owner_pk')
        # Redirect to admin_owner_profile page with the correct pk
        return redirect(reverse('admin_owner_profile', kwargs={'pk': owner_pk}))

    else:
        # If not a POST request, simply redirect to the owner's profile
        return redirect(reverse('admin_owner_profile', kwargs={'pk': pk}))


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
import requests  # For interacting with the Chatbase API

@user_passes_test(lambda u: u.is_superuser)  # Ensure only admins can access
def chatbot_dashboard(request):
    if request.method == 'POST':
        # Handle form submission to add/update chatbot responses
        question = request.POST['question']
        response = request.POST['response']
        
        # Example of a POST request to Chatbase API to update the bot's content
        url = "https://api.chatbase.com/v1/<endpoint>"
        headers = {'Authorization': 'Bearer <API_KEY>'}
        data = {
            "question": question,
            "response": response
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            # Success message
            return redirect('chatbot_dashboard')

    return render(request, 'admin/chatbot_dashboard.html')

#chatbot
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ChatbotResponse
from django.db.models import Q
import random
from datetime import datetime
from fuzzywuzzy import process  # Make sure you have this installed
from django.core.exceptions import ObjectDoesNotExist
import re
from .models import ChatConversation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
import random
from .joke_response import get_joke_response
from .emotional_support import provide_advice  # Adjust the import based on your project structure

# Detect agreement from user
def analyze_agreement(user_message):
    agreements = ['yes', 'sure', 'okay', 'of course', 'why not', 'another', 'tell me more joke', 'another joke', 'more joke', 'yeah', 'okay']
    return any(word in user_message.lower() for word in agreements)

# Detect joke request from user
def analyze_joke_request(user_message):
    joke_triggers = ['tell me a joke', 'give me a joke', 'joke please', 'can you tell me a joke', 'joke', 'tell me more joke', 'another joke', 'more joke']
    return any(trigger in user_message.lower() for trigger in joke_triggers)

@csrf_exempt
def process_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message')

        if request.user.is_authenticated:
            user = request.user
            context = request.session.get('chat_context', {})
            sia = SentimentIntensityAnalyzer()  # Initialize your sentiment analyzer

            # Analyze user's message for emotion and context
            emotion = check_for_keywords(user_message)
            bot_reply = ""

            if emotion:
                # Generate an empathetic response if emotional keywords are detected
                bot_reply = provide_emotional_support(user_message, context, sia)  # Should be a string
                context['last_topic'] = emotion  # Keep track of the emotion context
                
                # Provide advice if the conversation is about work or relevant topics
                advice = provide_advice(emotion, user_message)
                if advice:
                    bot_reply += " " + advice  # Append advice to the response

            elif analyze_joke_request(user_message):
                context['last_topic'] = 'jokes'  # Set topic to jokes
                bot_reply = get_joke_response(context)

            elif context.get('last_topic') == 'jokes':
                if analyze_agreement(user_message):
                    bot_reply = get_joke_response(context)
                else:
                    bot_reply = get_bot_response(user_message, user.id, request.session)
                    context['last_topic'] = None  # End the joke topic
                    context['jokes_told'] = []  # Reset jokes list

            else:
                # Handle normal bot responses for other conversations
                bot_reply = get_bot_response(user_message, user.id, request.session)
                context['jokes_told'] = []  # Reset jokes when changing topic
                context['last_topic'] = None  # Reset topic when out of joke context

            # Save updated context back to session
            request.session['chat_context'] = context

            # Log the conversation
            convo = ChatConversation.objects.create(
                user=user,
                user_message=user_message,
                bot_response=bot_reply
            )

            # Return the response
            response_data = {
                'id': convo.id,
                'reply': bot_reply,
                'timestamp': timezone.now().strftime('%b %d, %Y, %I:%M %p')
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'User not authenticated.'}, status=403)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

# Function to retrieve conversation history
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse

def get_chat_history(request):
    if request.method == 'GET':
        limit = int(request.GET.get('limit', 7))  # Number of messages to fetch
        offset = int(request.GET.get('offset', 0))  # Start point for fetching
        chat_history = ChatConversation.objects.filter(user=request.user).order_by('-timestamp')[offset:offset + limit]
        
        formatted_history = [
            {
                'id': chat.id,
                'user_message': chat.user_message,
                'bot_response': chat.bot_response,
                'timestamp': chat.timestamp.isoformat()
            }
            for chat in chat_history
        ]
        return JsonResponse({'chat_history': formatted_history, 'has_more': len(chat_history) == limit})

def save_feedback(request):
    if request.method == 'POST':
        conversation_id = request.POST.get('conversation_id')
        feedback_type = request.POST.get('feedback_type')

        print(f"Received conversation_id: {conversation_id}, feedback_type: {feedback_type}")  # Debug log

        if not conversation_id or not feedback_type:
            return JsonResponse({'status': 'error', 'message': 'Missing data.'}, status=400)

        try:
            conversation = ChatConversation.objects.get(id=conversation_id)
            feedback = ChatFeedback.objects.create(
                conversation=conversation,
                feedback_type=feedback_type
            )
            return JsonResponse({'status': 'success', 'message': 'Feedback saved successfully.'})
        except ChatConversation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Conversation not found.'}, status=404)
        except Exception as e:
            print(f"Error saving feedback: {str(e)}")  # Debug log
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


#remember name of the user
def handle_name_input(user_message, session):
    # Check for patterns indicating the user is stating their name
    name_patterns = [
        r"my name is (\w+)",        # Matches "My name is Kyle"
        r"call me (\w+)",            # Matches "Call me Kyle"
    ]

    for pattern in name_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            name = match.group(1)  # Extract the name
            session['user_name'] = name  # Store the name in the session context
            return f"Got it! I'll remember that your name is {name}."
    
    return None  # If no name is found, return None


def get_current_time_response():
    current_time = datetime.now().strftime("%I:%M %p")
    return f"The current time is {current_time}."

def get_current_date_response():
    current_date = datetime.now().strftime("%B %d, %Y")
    return f"Today's date is {current_date}."

def get_current_weather_response():
    current_weather = "sunny with a high of 75°F"
    return f"The current weather is {current_weather}."

def get_available_properties():
    properties = Property.objects.filter(availability='available')
    if not properties:
        return "There are currently no available properties."
    
    property_list = [
        f"Name: {prop.property_name}, Type: {prop.property_description}"
        for prop in properties
    ]
    
    return "Here are the available properties:\n" + "\n".join(property_list)

def get_latest_announcement():
    try:
        # Fetch the latest announcement
        latest_announcement = Announcement.objects.latest('created_at')
        return latest_announcement
    except ObjectDoesNotExist:
        return None

def get_my_property(user_id):
    try:
        # Fetch the homeowner by user ID
        user = User.objects.get(pk=user_id)
        owner = HomeOwner.objects.get(user=user)
        my_property = Property.objects.get(household_head=owner)
        
        # Check if the owner has an associated property
        if my_property:
            # Construct a dictionary or string with property details
            property_details = {
                "name": my_property.property_name,
                "availability": my_property.availability,
                "bedroom": my_property.bedroom,
                "bathroom": my_property.bathroom,
                "property_block_no": my_property.property_block_no,
                "property_house_no": my_property.property_house_no,
                "description": my_property.property_description,
                "lot_size": my_property.lot_size,
                "date_registered": my_property.date_registered.strftime("%b %d %Y"), 
                # Add other fields as needed
            }
            return property_details
        else:
            return None  # No associated property
        
    except ObjectDoesNotExist:
        return None  # Owner with this user_id does not exist
    except Exception as e:
        # Optionally log the exception or handle other unexpected errors
        print(f"An error occurred: {e}")
        return None

def get_support_team_contact_info():
    try:
        # Assuming there's only one secretary and one admin
        secretary = Secretary.objects.first()  # Get the first secretary
        admin = User.objects.get(is_superuser=True)  # Get the admin user

        contact_info = {
            "phone": secretary.contact_number if secretary else "No secretary available",  # Replace with actual phone number if needed
            "email_secretary": secretary.email_address if secretary else "No secretary available",
            "email_admin": admin.email if admin else "No admin available",
            "hours": "Monday to Friday, 9 AM - 5 PM",
        }
        return contact_info
    except ObjectDoesNotExist:
        return {
            "phone": "+1234567890",  # Default phone number
            "email_secretary": "No secretary available",
            "email_admin": "No admin available",
            "hours": "Monday to Friday, 9 AM - 5 PM",
        }


from django.core import serializers

def get_latest_event():
    try:
        # Fetch the latest event
        latest_event = Event.objects.latest('date_created')

        # Create a dictionary with the event data you want to return
        event_data = {
            "id": latest_event.id,
            "title": latest_event.event_name,
            "date_created": latest_event.date_created.strftime('%Y-%m-%d %H:%M:%S'),
            # Add other fields as needed
        }

        # Return the data as a JsonResponse
        return JsonResponse(event_data)

    except ObjectDoesNotExist:
        return JsonResponse({"error": "No events found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_user_name(user_id):
    try:
        user = User.objects.get(id=user_id)
        # Ensure both first and last names are included, and handle empty names
        first_name = user.first_name if user.first_name else "User"
        last_name = user.last_name if user.last_name else ""
        full_name = f"{first_name} {last_name}".strip()
        return full_name or "User"  # Fallback if full_name is empty
    except User.DoesNotExist:
        return "User"  # Fallback for non-existent user

def get_user_maintenance_requests(user_id):
    # Fetch maintenance requests for the user with pending or in progress status
    requests = Maintenance_request.objects.filter(name_of_owner__id=user_id)
    requestCount = requests.count()
    if not requests:
        return "You have no maintenance requests."
    else:
        # Format the response for each request
        request_list = [
            f"• Request ID: {req.id}\n   Description: {req.Description_of_issue}\n   Status: {req.status}\n   Requested on: {req.date_requested.strftime('%B %d, %Y')}\n"
            for req in requests
        ]
        response = f"Here are your maintenance requests({requestCount}):\n" + "\n".join(request_list)
        return response

# Updated check_maintenance_count function
def check_maintenance_count(user_id):
    # Fetch user's active maintenance requests (pending or in-progress)
    pending_requests = Maintenance_request.objects.filter(
        name_of_owner__id=user_id,
        status='Pending'
    )
    in_progress_requests = Maintenance_request.objects.filter(
        name_of_owner__id=user_id,
        status='In progress'
    )
    done_requests = Maintenance_request.objects.filter(
        name_of_owner__id=user_id,
        status='Done'
    )
    verified_requests = Maintenance_request.objects.filter(
        name_of_owner__id=user_id,
        status='Verified'
    )
    notverified_requests = Maintenance_request.objects.filter(
        name_of_owner__id=user_id,
        status='notverified'
    )

    total_request = Maintenance_request.objects.filter(name_of_owner__id=user_id).count()

    # Count requests
    pending_count = pending_requests.count()
    in_progress_count = in_progress_requests.count()
    done_count = done_requests.count()
    verified_count = verified_requests.count()
    notverified_count = notverified_requests.count()

    # Generate the URL for the maintenance request list
    maintenance_url = reverse('request_maintenance_list')

    # Prepare the response with counts and details
    response = f"""You currently have a total of {total_request} requests:
    • {pending_count} Pending.
    • {in_progress_count} In progress.
    • {done_count} Done.
    • {verified_count} Verified.
    • {notverified_count} Not Verified.

    You can view your full list of maintenance requests by visiting the request page: 
    <a class='underline text-sm text-teal-500' href="{maintenance_url}">View Maintenance Requests</a>
"""
    return response
    
from ADMIN.request_a_maintenance import handle_maintenance_request
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from ADMIN.emotional_support import provide_emotional_support, check_for_keywords

# Initialize the sentiment analyzer
sia = SentimentIntensityAnalyzer()

def get_bot_response(user_message, user_id, session):

    context = {}

    # Check for emotional or keyword triggers
    keyword_trigger = check_for_keywords(user_message)

    if keyword_trigger:
        if keyword_trigger in ['positive', 'negative']:
            # Trigger emotional support response if positive or negative emotion is detected
            emotion_response = provide_emotional_support(user_message, context, sia)
            if emotion_response:
                return emotion_response
        
        # Trigger responses based on specific issues like work, health, relationships, etc.
        if keyword_trigger == 'work':
            session['last_topic'] = 'work'
            return "It sounds like you're having some work stress. What's going on at work?"
        elif keyword_trigger == 'relationship':
            session['last_topic'] = 'relationship'
            return "Relationship problems can be tough. Do you want to talk about it?"
        elif keyword_trigger == 'health':
            session['last_topic'] = 'health'
            return "Health is important. Is there something in particular that you're feeling unwell about?"
        elif keyword_trigger == 'financial':
            session['last_topic'] = 'financial'
            return "Money problems can be stressful. Would you like to discuss how you're managing your finances?"
        elif keyword_trigger == 'maintenance':
            session['last_topic'] = 'maintenance'
            return "Are you facing maintenance issues? I can help you with that. Please specify the problem (e.g., plumbing, electrical, etc.)."


    # Call the maintenance request handler
    response = handle_maintenance_request(user_message, user_id, session)
    if response:
        return response

    # Check if the user asks about maintenance requests
    if 'many maintenance requests' in user_message.lower() or \
       'maintenance count' in user_message.lower() or \
       'active maintenance requests' in user_message.lower() or \
       'what maintenance requests do I have' in user_message.lower():
        return check_maintenance_count(user_id)

    # Check for name input first
    name_response = handle_name_input(user_message, session)
    if name_response:
        return name_response

     # Check if the user is asking for their name
    if re.search(r"what is my name\?", user_message, re.IGNORECASE):
        name = session.get('user_name', None)
        if name:
            return f"Your name is {name}."
        else:
            return "I don't know your name yet. Please tell me!"
    
    # Ensure the session context has been initialized
    if 'context' not in session:
        session['context'] = {
            'last_topic': None,
            'user_name': None,
            'preferences': {},
            'conversation_history': []  # Initialize conversation history
        }

    context = session['context']

    # Ensure conversation_history is initialized
    if 'conversation_history' not in context:
        context['conversation_history'] = []  # Initialize if not present

    # Normalize the user message: lower case and remove specific punctuation
    normalized_message = user_message.lower().replace('?', '').strip()
    
    # Add the user's message to the conversation history
    context['conversation_history'].append({'user_message': user_message})  # Append user's message to history

    # Check for user introduction
    if normalized_message in ['my name is ', 'no, my name is ', 'i am ', 'im']:
        context['user_name'] = user_message.split("my name is")[-1].strip()
        session['context'] = context
        return f"Nice to meet you, {context['user_name']}!"

    # Handle specific queries
    if normalized_message in ['tell me the time', 'what time is it?', 'time', 'time now', 'current time', 'what is the time', 'time?']:
        return get_current_time_response()
    
    if normalized_message in ['what is the date today', 'date', 'date today', 'date now', 'whats the date today']:
        return get_current_date_response()

    if normalized_message in ['what is the weather now', 'weather']:
        return get_current_weather_response()

    if normalized_message in ['available properties', 'properties']:
        return get_available_properties()

    # Handle user name queries
    if normalized_message in ['what is my real name', 'can you tell me my name', 'my real name', 'who am i', 'please tell me my name', 'what is my name']:
        user_name = get_user_name(user_id)  # Call the function to get the user's name
        return f"Your name is {user_name}." if user_name else "I'm sorry, I couldn't find your name."

    # Check for property maintenance status
    if normalized_message in ["my maintenance request list", "maintenance list", "request list", "my request list", "maintenance request list", "request maintenance list", "is my house under repair", "requests i submit", "maintenances i submit", "list of maintenances i requested"]:
        return get_user_maintenance_requests(user_id)

    # Check if the normalized message matches any maintenance inquiry
    if normalized_message in ['about my property', 'my property', 'my house', 'about my unit']:
        property_details = get_my_property(user_id)
        if property_details:
            response_message = (
                f"Here is the information about your property:\n"
                f"Property Name: {property_details['name']}\n"
                f"Bedroom: {property_details['bedroom']}\n"
                f"Bathroom: {property_details['bathroom']}\n"
                f"Block no.: {property_details['property_block_no']}\n"
                f"House no.: {property_details['property_house_no']}\n"
                f"Availability: {property_details['availability']}\n"
                f"Description: {property_details['description']}\n"
                f"Lot Size: {property_details['lot_size']} m² \n"
                f"Date registered: {property_details['date_registered']}\n"
            )
            return response_message
        else:
            return "You don't have a property in your account yet."

    elif normalized_message in ['contact info', 'support team contact info', 'contact support', 'team contact information', 'contacts', 'contact', 'contact for help']:
        contact_info = get_support_team_contact_info()
        response_message = (
            f"Support Team Contact Information:\n"
            f"Phone: {contact_info['phone']}\n"
            f"Secretary Email: {contact_info['email_secretary']}\n"
            f"Admin Email: {contact_info['email_admin']}\n"
            f"Hours: {contact_info['hours']}\n"
        )
        return response_message
    
    announcement_prompts = ['latest announcement', 'announcements', 'show announcements', 'announcement', 'any announcements?', 'tell me announcements']

    if any(prompt in user_message.lower() for prompt in announcement_prompts):
        latest_announcement = get_latest_announcement()
        if latest_announcement:
            response_message = (
                f"Latest Announcement:\n"
                f"Title: {latest_announcement.title} \n"
                f"Content: {latest_announcement.content[:100]} \n\n"
                f"To view announcements, you can check the announcement section in the sidebar."
            )
            return response_message
        else:
            return "There are no announcements at the moment."

    if user_message.lower() in ["latest events", "event", "events", 'community events', 'events in', 'upcoming events']:
        return 'I cannot fetch the events yet. But you can try to check the event section on your dashboard or on the sidebar panel.'

    # General conversational fallback
    responses = [
        "That's interesting! Can you tell me more?",
        "I see! What else would you like to talk about?",
        "That's great! Do you have any other questions?",
        "I'm here to chat! What would you like to discuss next?",
    ]

    # Try exact matching
    all_queries = ChatbotResponse.objects.values_list('user_query', flat=True)
    if user_message in all_queries:
        responses = ChatbotResponse.objects.filter(user_query=user_message).values_list('bot_response', flat=True)
        if responses:
            return random.choice(responses)

    # Fuzzy matching for broader responses
    closest_match, score = process.extractOne(user_message, all_queries)
    if score >= 70:
        responses = ChatbotResponse.objects.filter(user_query=closest_match).values_list('bot_response', flat=True)
        if responses:
            return random.choice(responses)

    # If no match, use the fallback
    return random.choice(responses)  # Return a general conversational prompt


# Functions like get_current_time_response(), get_current_date_response(), etc. remain the same
#prompt suggestions
# 1. About my property
# 2. Upcoming events
# 3. Latest Announcements
# 4. Submit maintenance request
# 5. Support team contact info

def submit_chatFeedback(request):
    if request.method == 'POST':
        bot_response = request.POST.get('bot_response')
        feedback_type = request.POST.get('feedback')
        
        # Find the latest chat conversation with the same bot response
        chat_convo = ChatConversation.objects.filter(bot_response=bot_response).last()

        # Store feedback
        if chat_convo:
            ChatFeedback.objects.create(
                conversation=chat_convo,
                feedback_type=feedback_type
            )
        
        return JsonResponse({'status': 'success', 'message': 'Feedback submitted successfully.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)


