from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from USERS.models import HomeOwner, Resident
from .models import Secretary, Event, Comment, Property, Message, MaintenancePersonnel, AdminNotification, Log, PropertyImage, Announcement, AnnouncementComment, PaymentReminder, ChatFeedback, ChatHistoryMessage, VisitRequest, PropertyModel, EmergencyContact
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

@login_required
def analytics(request):
    return render(request, 'analytics.html')

from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render
from matplotlib import pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter, WeekdayLocator
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth, TruncWeek
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncWeek

def dashboard_graphs_data(request):
   # Weekly Maintenance Requests
    current_year = timezone.now().year
    start_date = timezone.now() - timedelta(weeks=12)  # Limit to last 12 weeks if desired

    weekly_maintenance = (
        Maintenance_request.objects
        .filter(date_requested__year=current_year, date_requested__gte=start_date)
        .annotate(week=TruncWeek('date_requested'))
        .values('week')
        .annotate(count=Count('id'))
        .order_by('week')
    )
    
    # Weekly Visit Requests
    start_date = timezone.now() - timedelta(weeks=12)
    weekly_visits = (
        VisitRequest.objects
        .filter(created_at__gte=start_date)
        .annotate(week=TruncWeek('created_at'))
        .values('week')
        .annotate(count=Count('id'))
        .order_by('week')
    )
    
    # Total and Occupied Properties
    total_properties = Property.objects.all().count()
    occupied_properties = Property.objects.filter(availability='occupied').count()

    # Prepare data for JSON response
    data = {
        "weekly_maintenance": {
            "weeks": [entry['week'].strftime('%b') for entry in weekly_maintenance],
            "counts": [entry['count'] for entry in weekly_maintenance],
        },
        "weekly_visits": {
            "weeks": [entry['week'].strftime('%b %d') for entry in weekly_visits],
            "counts": [entry['count'] for entry in weekly_visits],
        },
        "properties": {
            "labels": ["Occupied", "Available"],
            "sizes": [occupied_properties, total_properties - occupied_properties],
        }
    }

    return JsonResponse(data)


# def dashboard_graphs(request):
#     # Monthly Maintenance Requests
#     current_year = datetime.now().year
#     monthly_maintenance = (
#         Maintenance_request.objects
#         .filter(date_requested__year=current_year)
#         .annotate(month=TruncMonth('date_requested'))
#         .values('month')
#         .annotate(count=Count('id'))
#         .order_by('month')
#     )

#     # Weekly Visit Requests
#     start_date = datetime.now() - timedelta(weeks=12)  # last 12 weeks
#     weekly_visits = (
#         VisitRequest.objects
#         .filter(created_at__gte=start_date)
#         .annotate(week=TruncWeek('created_at'))
#         .values('week')
#         .annotate(count=Count('id'))
#         .order_by('week')
#     )

#     # Count Total and Occupied Properties
#     total_properties = Property.objects.all().count()
#     occupied_properties = Property.objects.filter(availability='occupied').count()

#     # Prepare the pie chart data
#     property_labels = ['Occupied', 'Available']
#     property_sizes = [occupied_properties, total_properties - occupied_properties]  # Available count

#     # Plot Monthly Maintenance Requests and Weekly Visit Requests
#     fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))  # Unpack into three axes

#     # Monthly Maintenance Requests
#     months = [entry['month'] for entry in monthly_maintenance]
#     maintenance_counts = [entry['count'] for entry in monthly_maintenance]
    
#     ax1.plot(months, maintenance_counts, marker='o', color='b', label="Maintenance Requests")
#     ax1.xaxis.set_major_locator(MonthLocator())
#     ax1.xaxis.set_major_formatter(DateFormatter('%b'))
#     ax1.set_xlabel("Month")
#     ax1.set_ylabel("Number of Requests")
#     ax1.set_title("Maintenance Requests per Month")
#     ax1.grid(True)

#     # Weekly Visit Requests
#     weeks = [entry['week'] for entry in weekly_visits]
#     visit_counts = [entry['count'] for entry in weekly_visits]
    
#     ax2.plot(weeks, visit_counts, marker='o', color='g', label="Visit Requests")
#     ax2.xaxis.set_major_locator(WeekdayLocator())
#     ax2.xaxis.set_major_formatter(DateFormatter('%b %d'))
#     ax2.set_xlabel("Week")
#     ax2.set_ylabel("Number of Requests")
#     ax2.set_title("Visit Requests per Week")
#     ax2.grid(True)

#     # Plot Occupied vs Available Properties
#     ax3.pie(property_sizes, labels=property_labels, autopct='%1.1f%%', startangle=140, colors=['#66b3ff', '#ff9999'])
#     ax3.axis('equal')  # Equal aspect ratio ensures pie chart is circular
#     ax3.set_title("Occupied vs Available Properties")

#     # Save plot to response
#     response = HttpResponse(content_type='image/png')
#     plt.tight_layout()
#     plt.savefig(response, format='png')
#     plt.close(fig)
    
#     return response


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

            messages.success(request, 'Repairman added successfully')
            return JsonResponse({
                'success': True,
                'message': 'Repairman added successfully'  # Success message
            })
        else:
            print(form.errors)  # Debugging - Log form errors
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })  # Return validation errors

    return JsonResponse({'success': False, 'message': 'Invalid request'})

def admin_edit_personnel(request, pk):
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
            description=f"Admin '{request.user}' updated personnel '{personnel.name}'.",
            user=request.user,
            action=f"Old data: {old_data} -> New data: {request.POST}"  # Optional: log old vs new data
        )

        messages.success(request, 'Personnel details updated successfully!')
        return redirect('admin_maintenance_personnel_list')  # Replace with your actual redirect route

def admin_delete_personnel(request, pk):
    personnel = get_object_or_404(MaintenancePersonnel, pk=pk)
    
    if request.method == 'POST':
        personnel_name = personnel.name  # Store name for logging before deletion
        personnel.delete()

        # Create a log entry
        Log.objects.create(
            log_type='warning',  # or 'info' depending on how you classify deletions
            description=f"Admin '{request.user}' deleted personnel '{personnel_name}'.",
            user=request.user,
            action=f"Deleted personnel '{personnel_name}'"
        )

        messages.success(request, 'Personnel deleted successfully!')
        return redirect('admin_maintenance_personnel_list')  # Replace with your actual redirect route

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
    # Retrieve filters from the GET request
    availability_filter = request.GET.get('availability')
    block_filter = request.GET.get('block')
    model_filter = request.GET.get('model')  # updated to match the `name` attribute in the select

    # Query all properties and property models
    properties = Property.objects.all()
    property_models = PropertyModel.objects.all()

    # Apply availability filter
    if availability_filter:
        properties = properties.filter(availability=availability_filter)

    # Apply block filter
    if block_filter:
        properties = properties.filter(property_block_no=block_filter)

    # Apply model filter, adjusting for the property model field
    if model_filter:
        properties = properties.filter(property_model=model_filter)  # Adjust `property_model__name` as needed

    # Query all property images for display
    property_images = PropertyImage.objects.all()

    # Handle form submission for adding a new property
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)

        if form.is_valid():
            # Create a new property instance but don't save it to the database yet
            new_property = form.save(commit=False)

            # Assign the property model based on the form data
            property_model_id = request.POST.get('property_model')
            if property_model_id:
                new_property.property_model_id = property_model_id
            
            # Save the new property instance to the database
            new_property.save()

            # Log the action for tracking
            Log.objects.create(
                log_type='info',
                description=f"Admin '{request.user}' added a new property: '{new_property.property_name}'.",
                user=request.user
            )

            # Return a JSON response for AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Property added successfully!'})

            # Redirect with success message for non-AJAX requests
            messages.success(request, 'Property added successfully!')
            return redirect('/properties/?message=Property added successfully!')

        else:
            # Return form errors as JSON for AJAX requests
            errors = form.errors.as_json()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': errors})
    else:
        # Initialize an empty form if the request is not a POST
        form = PropertyForm()

    # Render the properties page with filtering and form handling
    return render(request, 'properties.html', {
        'properties': properties,
        'form': form,
        'property_images': property_images,
        'availability_filter': availability_filter,
        'block_filter': block_filter,
        'property_models': property_models,
        'model_filter': model_filter
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

@login_required
def chat_logs(request):
    # Get all ChatConversation instances
    conversations = ChatConversation.objects.all().order_by('-timestamp')

    # Initialize the feedback variables
    feedback_likes = []
    feedback_dislikes = []

    # Check filter parameters from request
    show_likes = request.GET.get('likes', 'off') == 'on'
    show_dislikes = request.GET.get('dislikes', 'off') == 'on'

    # Get feedback if the filters are active
    if show_likes:
        feedback_likes = ChatFeedback.objects.filter(feedback_type='like').values_list('conversation_id', flat=True)

    if show_dislikes:
        feedback_dislikes = ChatFeedback.objects.filter(feedback_type='dislike').values_list('conversation_id', flat=True)

    # Prepare the conversation list with feedback information
    filtered_conversations = []
    for conversation in conversations:
        conversation_data = {
            'conversation': conversation,
            'has_like': conversation.id in feedback_likes,
            'has_dislike': conversation.id in feedback_dislikes
        }
        filtered_conversations.append(conversation_data)

    return render(request, 'chatbot_logs.html', {'conversations': filtered_conversations})

@login_required
def chat_edit(request, id):
    conversation = get_object_or_404(ChatConversation, id=id)
    if request.method == "POST":
        conversation.likes = request.POST.get('likes', conversation.likes)
        conversation.dislikes = request.POST.get('dislikes', conversation.dislikes)
        conversation.save()
        return redirect('chat_logs')
    return render(request, 'chat_logs.html', {'conversation': conversation})

@login_required
def chat_delete(request, id):
    conversation = get_object_or_404(ChatConversation, id=id)
    conversation.delete()
    return redirect('chat_logs')

# Detect agreement from user
def analyze_agreement(user_message):
    agreements = ['yes', 'sure', 'okay', 'of course', 'why not', 'another', 'tell me more joke', 'another joke', 'more joke', 'yeah', 'okay']
    return any(word in user_message.lower() for word in agreements)

# Detect joke request from user
def analyze_joke_request(user_message):
    joke_triggers = ['tell me a joke', 'give me a joke', 'joke please', 'can you tell me a joke', 'joke', 'tell me more joke', 'another joke', 'more joke']
    return any(trigger in user_message.lower() for trigger in joke_triggers)

import requests

CHATBASE_API_KEY = "d2c2aea8-fe02-4412-af7c-90214efa82d7"
CHATBASE_API_URL = "https://www.chatbase.co/api/v1/message"

def get_chatbase_response(user_message, user_id):
    payload = {
        'api_key': CHATBASE_API_KEY,
        'user_id': user_id,
        'message': user_message,
    }
    try:
        response = requests.post(CHATBASE_API_URL, json=payload)
        response_data = response.json()
        if response.status_code == 200:
            return response_data.get('reply', 'No reply received from Chatbase')
        else:
            return "Error: Unable to get a reply from Chatbase"
    except requests.RequestException as e:
        return f"Error: {str(e)}"


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
                    bot_reply = get_bot_response(user_message, user.id, request.session, request)
                    context['last_topic'] = None  # End the joke topic
                    context['jokes_told'] = []  # Reset jokes list

            else:
                # Handle normal bot responses for other conversations
                bot_reply = get_bot_response(user_message, user.id, request.session, request)
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
        # Get the first secretary (if available)
        secretary = Secretary.objects.first()

        # Get all superusers (admins)
        admins = User.objects.filter(is_superuser=True)

        if admins.exists():
            # Create a list of admin contact info
            admin_contacts = [f"{admin.first_name} {admin.last_name}: {admin.email}" for admin in admins]
            admin_contact_info = "Admin contacts: " + ", ".join(admin_contacts)
        else:
            admin_contact_info = "No admin found."

        # Prepare the contact info
        contact_info = {
            "phone": secretary.contact_number if secretary else "No secretary available",
            "email_secretary": secretary.email_address if secretary else "No secretary available",
            "admin_contacts": admin_contact_info,
            "hours": "Monday to Friday, 9 AM - 5 PM",
        }

        return contact_info

    except ObjectDoesNotExist:
        # Default contact info in case something goes wrong
        return {
            "phone": "+1234567890",
            "email_secretary": "No secretary available",
            "admin_contacts": "No admin available",
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
from fuzzywuzzy import process
from .response import responses

# Initialize the sentiment analyzer
sia = SentimentIntensityAnalyzer()

def get_bot_response(user_message, user_id, session, request):
    if any(keyword in user_message.lower() for keyword in ["emergency contacts", "emergency contact list", "show emergency contacts", "help contacts"]):
        # Fetch emergency contacts
        contacts = EmergencyContact.objects.all().values('name', 'department', 'phone')
        if contacts.exists():
            response_message = "Here are the emergency contacts:\n \n"
            for contact in contacts:
                response_message += (
                    f"- Name: {contact['name']}\n"
                    f"  Department: {contact['department']}\n"
                    f"  Phone: {contact['phone']}\n\n"
                )
            return response_message
        else:
            return "There are no emergency contacts available at the moment."

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

        # Make sure admin contacts are in a list format
        admin_contacts_list = contact_info['admin_contacts'] if isinstance(contact_info['admin_contacts'], list) else [contact_info['admin_contacts']]

        response_message = (
            "Support Team Contact Information: \n\n"
            "Here are the details of the support team:\n"
            "- Phone: {phone}\n"
            "- Secretary Email: {email_secretary}\n\n"
            "{admin_contacts}\n"
            "- Office Hours: {hours}\n\n"
            "Feel free to reach out during office hours for assistance."
        ).format(
            phone=contact_info['phone'],
            email_secretary=contact_info['email_secretary'],
            admin_contacts="\n  - ".join(admin_contacts_list),  # Ensure we join the list of contacts
            hours=contact_info['hours']
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

    # Retrieve all keys from the responses dictionary for exact and fuzzy matching
    user_message = user_message.lower()  # Normalize user input

    # Check for matches in your local system, or fallback to Chatbase if no match is found
    chatbase_response = get_chatbase_response(user_message, request)
    if chatbase_response:
        return chatbase_response

    # If no match was found, return a fallback response
    return "I'm not sure how to respond to that."  # Default response

# Replace with your Chatbase API key
CHATBASE_API_KEY = 'd2c2aea8-fe02-4412-af7c-90214efa82d7'  # Your Chatbase API Key
CHATBOT_ID = 'JiPiv2wOvAUbPJA6DJ2Tx'  # Your Chatbase chatbot ID

import json

# Function to get response from Chatbase
def get_chatbase_response(user_message, request):
    chatbase_api_url = 'https://www.chatbase.co/api/v1/chat'  # Chatbase API endpoint
    
    # Prepare the payload for the Chatbase request
    payload = {
        "messages": [
            {"content": user_message, "role": "user"}
        ],
        "chatbotId": CHATBOT_ID,
        "stream": False,
        "temperature": 0.5,
        "model": "gpt-4o",
    }

    headers = {
        'Authorization': f'Bearer {CHATBASE_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    try:
        # Send the message to Chatbase API
        response = requests.post(chatbase_api_url, headers=headers, json=payload)
        
        # Log response status and content for debugging
        print("Response status code:", response.status_code)
        print("Response content:", response.text)
        
        # Check if the response contains JSON data
        if response.status_code == 200:
            try:
                # Parse the JSON response
                response_data = response.json()
                
                # Extract the text response from the JSON structure
                chatbase_response = response_data.get("text", "I'm sorry, I couldn't understand that.")
                
                return chatbase_response
            except json.JSONDecodeError:
                print("Error: Response is not valid JSON")
                return "Sorry, the response from Chatbase could not be processed."
        else:
            # Log error details if status code is not 200
            print("Error: Non-200 status code received.")
            return f"Error from Chatbase: {response.status_code} - {response.text}"
    except requests.RequestException as e:
        print(f"Error connecting to Chatbase: {e}")
        return "Sorry, I encountered a connection error while processing your request."


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


def admin_emergency_contact(request):
    name = ""
    department = ""
    phone = ""
    
    if request.method == 'POST':
        name = request.POST.get('name')
        department = request.POST.get('department')
        phone = request.POST.get('phone')

        if not name and department and phone:
            messages.error(request, 'All fields are required')
        else:
            EmergencyContact.objects.create(
                name=name,
                department=department,
                phone=phone
            )
            messages.success(request, 'Emergency contact saved!')
            return redirect('admin_emergency_contact')

    emergency_contacts = EmergencyContact.objects.all()
    return render(request, 'admin_emergency_contact.html', {'emergency_contacts':emergency_contacts, 'name':name, 'department':department, 'phone':phone})

def edit_contact(request, contact_id):
    contact = get_object_or_404(EmergencyContact, id=contact_id)
    if request.method == 'POST':
        contact.name = request.POST.get('name')
        contact.department = request.POST.get('department')
        contact.phone = request.POST.get('phone')
        contact.save()
        messages.success(request, 'Contact updated successfully!')
        return redirect('admin_emergency_contact')
    messages.error(request, 'Invalid request.')
    return redirect('admin_emergency_contact')


def delete_contact(request, contact_id):
    contact = get_object_or_404(EmergencyContact, id=contact_id)
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Contact deleted successfully!')
        return redirect('admin_emergency_contact')
    messages.error(request, 'Invalid request.')
    return redirect('admin_emergency_contact')

def admin_live_chat(request):
    return render(request, 'admin_live_chat.html')

@login_required
def admin_get_unread_messages_count(request):
    unread_count = Message.objects.filter(
        is_read=False
    ).exclude(sender=request.user.username).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def admin_mark_all_messages_as_read(request):
    # Mark all messages sent to the current user as read
    Message.objects.filter(
        is_read=False
    ).exclude(sender=request.user.username).update(is_read=True)
    return JsonResponse({'status': 'success'})

@csrf_exempt
def admin_post_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message')
        sender = data.get('sender')

        if message and sender:
            Message.objects.create(message=message, sender=sender)
            return JsonResponse({'status': 'success'}, status=200)
    return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

def admin_get_new_messages(request):
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