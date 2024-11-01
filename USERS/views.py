from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect 
from .models import HomeOwner, Resident
from HOMEOWNER.models import Activitie, Maintenance_request
from .forms import UserForm, HomeOwnerForm, OwnerLoginForm, SecretaryLoginForm
from ADMIN.models import Secretary, Event, Log, Property, VisitRequest
from django.contrib import messages
from HOMEOWNER.models import Notification
from SECRETARY.signals import create_homeowner_notification
from ADMIN.signals import admin_create_homeowner_notification
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.conf import settings
from .forms import PasswordResetRequestForm
from .models import PasswordResetToken
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from dateutil import parser
from django.utils import timezone


# views.py
from django.http import JsonResponse


def homepage(request):
    properties = Property.objects.select_related('household_head').all().order_by('property_house_no')
    return render(request, 'homepage.html', {'properties':properties})

def get_target_coordinates(request):
    # Example coordinates for the target point (update with your values or database values)
    target_coordinates = {
        "x": 10,
        "y": 5,
        "z": -15
    }
    return JsonResponse(target_coordinates)

def submit_visit_request(request):
    if request.method == 'POST':
        try:
            # Load JSON data from the request body
            data = json.loads(request.body)

            # Extract the required fields
            visitor_full_name = data.get('visitor_full_name')
            visitor_relation = data.get('visitor_relation')
            visit_date_string = data.get('visit_date')
            purpose = data.get('purpose')
            household_head_name = data.get('household_head')

            # Validate required fields
            if not all([visitor_full_name, visitor_relation, visit_date_string, purpose, household_head_name]):
                return JsonResponse({'error': 'All fields are required.'}, status=400)

            # Convert visit date to timezone-aware format
            visit_date = timezone.make_aware(parser.parse(visit_date_string))

            # Fetch the HomeOwner instance based on the household head's username
            try:
                household_head = HomeOwner.objects.get(user__username=household_head_name)
            except HomeOwner.DoesNotExist:
                return JsonResponse({'error': 'Household head not found.'}, status=404)

            # Create and save the visit request
            visit_request = VisitRequest(
                visitor_full_name=visitor_full_name,
                visitor_relation=visitor_relation,
                visit_date=visit_date,
                purpose=purpose,
                household_head=household_head,
            )
            visit_request.save()  # Save the visit request to the database

            # Store visitor's full name in session for future filtering
            request.session['visitor_full_name'] = visitor_full_name

            # Get homeowner's full name and email
            owner_full_name = f"{household_head.user.first_name} {household_head.user.last_name}"
            homeowner_email = household_head.user.email

            # Log the visit request creation
            log_entry = Log(
                log_type='info',
                description=f"Visitor '{visitor_full_name}' requested a visit to '{owner_full_name}' on {visit_date}.",
                user=household_head.user,
                action='Created Visit Request'
            )
            log_entry.save()  # Save the log entry to the database

            # Send an email to the household head regarding the visit request
            send_email_to_household_head(
                owner_full_name, visitor_full_name, visitor_relation, visit_date, purpose, homeowner_email
            )

            messages.success(request, 'Visit request submitted successfully!')
            return JsonResponse({'message': 'Visit request submitted successfully!'}, status=200)

        except ValueError as ve:
            # Handle date parsing errors
            return JsonResponse({'error': f'Invalid date format: {str(ve)}'}, status=400)
        except json.JSONDecodeError:
            # Handle JSON decoding errors
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            # General error handler for unexpected issues
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

    # Return a method not allowed error for non-POST requests
    return JsonResponse({'error': 'Invalid request method.'}, status=405)


def send_email_to_household_head(owner_full_name, visitor_name, relation, visit_date, purpose, recipient_email):
    subject = "New Visitor Request - Confirmation Needed"
    message = (
        f"Dear {owner_full_name},\n\n"
        f"A new visitor request has been submitted with the following details:\n\n"
        f"Visitor Name: {visitor_name}\n"
        f"Relation to Household: {relation}\n"
        f"Scheduled Visit Date: {visit_date}\n"
        f"Purpose of Visit: {purpose}\n\n"
        "Please review this request and confirm whether it should be approved.\n\n"
        "Thank you,\nYour Security Team"
    )
    send_mail(subject, message, 'bbvhhousingmanagement@gmail.com', [recipient_email])


def map(request):
    # Get the filter type from the query parameters; default to 'houses'
    filter_type = request.GET.get('filter', 'houses')

    # Retrieve properties or events based on the filter type
    if filter_type == 'houses':
        labels = Property.objects.select_related('household_head').all().order_by('property_house_no')
    elif filter_type == 'events':
        labels = Event.objects.all()
    else:
        labels = Property.objects.select_related('household_head').all().order_by('property_house_no')  # Fallback to properties

    # Retrieve the visitor's full name from the session
    visitor_full_name = request.session.get('visitor_full_name')

    # Filter visit requests based on the visitor's full name if it exists
    visit_requests = VisitRequest.objects.filter(visitor_full_name=visitor_full_name) if visitor_full_name else None

    return render(request, 'map.html', {
        'labels': labels,    # Either properties or events
        'visit_requests': visit_requests,
        'filter_type': filter_type
    })


def main(request):
    return render(request, 'main.html')

from django.utils import timezone
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserForm, VerificationForm, CompleteRegistrationForm
import random
import logging
from django.core.mail import EmailMultiAlternatives
from django.utils.html import format_html

logger = logging.getLogger(__name__)

def register(request):
    step = request.POST.get('step', '1')  # Default to step 1 if not provided
    form = UserForm()  # Initialize the form at the beginning

    if request.method == 'POST':
        if step == '1':  # First step: Collect first name, last name, and email
            form = UserForm(request.POST)
            
            if form.is_valid():
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                email = form.cleaned_data['email']

                # Store values in the session
                request.session['first_name'] = first_name
                request.session['last_name'] = last_name
                request.session['email'] = email

                # Generate and save verification code
                code = random.randint(100000, 999999)
                request.session['verification_code'] = code
                request.session.set_expiry(300)  # Set session to expire in 5 minutes

                # Create the email content
                subject = 'Your Verification Code'
                body = format_html(
                    '''
                    <p>Hello,</p>
                    <p>Thank you for registering with us! To complete your registration, please use the following verification code:</p>
                    <p style="font-weight: bold; font-size: 1.5em;">Verification Code: {}</p>
                    <p>Please enter this code on the verification page to proceed. If you did not request this code, please disregard this email.</p>
                    <p>If you have any questions or need assistance, feel free to reach out to our support team.</p>
                    <p>Best regards,<br>The Beta Bayview Team</p>
                    '''.format(code)
                )

                # Send the email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=body,  # This is still in plain text, see the next step
                    from_email='no-reply@example.com',
                    to=[email]
                )

                # Attach the HTML version
                email.attach_alternative(body, "text/html")

                # Send the email
                email.send(fail_silently=False)

                email_user = request.session.get('email')

                # Proceed to step 2: Verification code entry
                return render(request, 'verify_email.html', {'email': email_user})
            else:
                logger.warning("UserForm is not valid: %s", form.errors)

        elif step == '2':  # Second step: Verify the code
            mess = ""
            code1 = request.POST.get('code1', '')
            code2 = request.POST.get('code2', '')
            code3 = request.POST.get('code3', '')
            code4 = request.POST.get('code4', '')
            code5 = request.POST.get('code5', '')
            code6 = request.POST.get('code6', '')

            verification_code = ''.join([code1, code2, code3, code4, code5, code6])  # Combine the individual codes

            if verification_code and int(verification_code) == request.session.get('verification_code'):
                # Clear verification code after success
                del request.session['verification_code']
                return render(request, 'register_complete.html', {'form': CompleteRegistrationForm()})
            else:
                mess = 'Invalid verification code. Please try again.'
                # Re-render the verification page with the email address
                email = request.session.get('email')
                return render(request, 'verify_email.html', {'email': email, 'mess':mess})   
        
        elif step == '3':  # Final step: Complete registration with username and password
            form = CompleteRegistrationForm(request.POST)
            
            if form.is_valid():
                user = form.save(commit=False)

                # Fetch session data and set to user fields
                user.email = request.session.get('email')
                user.first_name = request.session.get('first_name')
                user.last_name = request.session.get('last_name')

                # Ensure all fields are not None before saving
                if not all([user.email, user.first_name, user.last_name]):
                    messages.error(request, "Registration data is missing. Please try again.")
                    return redirect('register')  # Redirect to start if data is missing

                user.save()

                # Create HomeOwner and log entry
                homeowner = HomeOwner.objects.create(user=user, pending=True)
                Log.objects.create(
                    log_type='info',
                    description=f'New homeowner registered for pending: {homeowner.user.username}.',
                    user=None
                )
                return redirect('register_success')  # Change to your success page
            
            else:
                # Log warning and add error messages
                logger.warning("CompleteRegistrationForm is not valid: %s", form.errors)
                # for field, errors in form.errors.items():
                #     for error in errors:
                #         messages.error(request, f"{field.capitalize()}: {error}")
                        
                # Re-render the form with errors to indicate required fields were not completed
                return render(request, 'register_complete.html', {'form': form})

        else:
            form = UserForm()  # Initial form for the first step
            
    # Render the initial registration form
    return render(request, 'register.html', {'form': form, 'step': step})

def register_success(request):
    return render(request, 'register_success.html')

def ownerLogin(request):
    message = request.GET.get('message', None)
    username = ''
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if HomeOwner.objects.filter(user=user).exists():
                homeowner = HomeOwner.objects.get(user=user)
                
                if not homeowner.pending:
                    login(request, user)
                    messages.success(request, 'Login successfully!')

                    # Create a success login log
                    Log.objects.create(
                        log_type='success',
                        description=f'Homeowner "{user.username}" logged in successfully.',
                        user=user
                    )
                    return redirect('owner_dashboard')
                else:
                    messages.warning(request, 'Your account is in pending approval')
                    # Log pending account warning (optional)
                    Log.objects.create(
                        log_type='warning',
                        description=f'Homeowner "{user.username}" attempted to log in but account is pending.',
                        user=user
                    )
            else:
                messages.error(request, 'Incorrect credentials')
        else:
            messages.error(request, 'Incorrect credentials')
            # Create a failed login log
            

            Log.objects.create(
                log_type='error',
                description=f'Homeowner "{username}" login failed: invalid credentials.',
                user=None  # Set user to None or you can use username here
            )

    return render(request, 'ownerLogin.html', {'message': message, 'username': username})

@login_required
def owner_dashboard(request):
    try:
        user = User.objects.get(username=request.user)
        homeowner = HomeOwner.objects.get(user=user)
        profile = homeowner.profile_picture.url
        totalResidents = Resident.objects.filter(household_representative=user).all()
        totalMaintenanceReq = Maintenance_request.objects.filter(name_of_owner=user).all()
        activities = Activitie.objects.filter(name_of_owner=user).all().order_by('-date')
        events = Event.objects.all()
        notifications = Notification.objects.filter(homeowner=user).order_by('-created_at')

        if Property.objects.filter(household_head=homeowner).exists():
            my_property = Property.objects.get(household_head=homeowner)
        else:
            my_property = None
        
    except HomeOwner.DoesNotExist:
        homeowner = None
        profile = None
        activities = None
        totalResidents = None
        totalMaintenanceReq = None
        events = None
        notifications = None
    return render(request, 'owner_dashboard.html', {'profile':profile, 'activities':activities, 'totalResidents':totalResidents, 'totalMaintenanceReq':totalMaintenanceReq, 'events':events, 'notifications':notifications, 'my_property':my_property})

def check_property(request):
    user = request.user  # Assuming the user is authenticated
    has_property = False
    property_id = None

    # Check if the property exists
    if Property.objects.filter(household_head=user.homeowner).exists():
        my_property = Property.objects.get(household_head=user.homeowner)
        has_property = True
        property_id = my_property.id

    # Return JSON response
    return JsonResponse({'has_property': has_property, 'property_id': property_id})

def ownerLogout(request):
    if request.user.is_authenticated:
        print(f"Logging out user: {request.user.username}")
        Log.objects.create(
            log_type='success',
            description=f'Homeowner {request.user.username} logged out successfully.',
            user=request.user
        )
    else:
        print("User is not authenticated")

    logout(request)  # Log the user out
    return redirect('main')



def secretaryLogin(request):
    message = request.GET.get('message', None)
    username = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if Secretary.objects.filter(user=user).exists():
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successfully!')

                # Create a success login log
                Log.objects.create(
                    log_type='success',
                    description=f'Secretary "{request.user}" logged in successfully.',
                    user=user
                )

                return redirect('secretary_dashboard')
            else:
                messages.error(request, 'Incorrect credentials.')
        else:
            messages.error(request, 'Incorrect credentials.')
    return render(request, 'secretaryLogin.html', {'message':message, 'username':username})

def secretaryLogout(request):
    if request.user.is_authenticated:
        print(f"Logging out user: {request.user.username}")
        Log.objects.create(
            log_type='success',
            description=f"Secretary '{request.user.username}' logged out successfully.",
            user=request.user
        )
    else:
        print("User is not authenticated")

    logout(request)  # Log the user out
    return redirect('main')

def adminLogin(request):
    username = ''
    password = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.warning(request, 'Both username and password are required.')
        else:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_superuser:
                    login(request, user)

                    # Create a success login log
                    Log.objects.create(
                        log_type='success',
                        description=f'Admin with username "{user.username}" logged in successfully.',
                        user=user
                    )
                    return redirect('admin_dashboard')  # Replace 'admin_dashboard' with your actual admin dashboard URL name
                else:
                    messages.error(request, 'Incorrect credentials')
                     # Create a failed login log
                    userLog = User.objects.get(username=username)

                    if userLog:
                        userToLog = userLog
                    else:
                        userToLog = None

                    Log.objects.create(
                        log_type='warning',
                        description=f' "{username}" login failed: not authorized to access the admin area.',
                        user=userToLog  # Set user to None or you can use username here
                    )
            else:
                messages.error(request, 'Incorrect credentials')
                 # Create a failed login log

                Log.objects.create(
                    log_type='error',
                    description=f'Admin with username "{username}" login failed: invalid credentials.',
                    user=None  # Set user to None or you can use username here
                )

    return render(request, 'adminLogin.html', {'username':username, 'password':password})

def adminLogout(request):
    if request.user.is_authenticated:
        print(f"Logging out user: {request.user.username}")
        Log.objects.create(
            log_type='success',
            description=f'Admin with username "{request.user.username}" logged out successfully.',
            user=request.user
        )
    else:
        print("User is not authenticated")

    logout(request)  # Log the user out
    return redirect('main')
	

def ar_view(request):
    return render(request, 'arMap.html')

def password_reset_request2(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = get_random_string(50)
                
                # Save token in the database
                reset_token = PasswordResetToken.objects.create(user=user, token=token)
                reset_token.save()

                # Send email
                reset_url = request.build_absolute_uri(f'/reset-password/{token}/')
                send_mail(
                    'Password Reset Request',
                    f'Hello {user.username},\n\nUse the link below to reset your password:\n{reset_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                messages.success(request, 'An email has been sent with password reset instructions.')
                return redirect('password_reset_request2')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email.')
                return redirect('password_reset_request2')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'password_reset_request2.html', {'form': form})


# views.py
from .forms import PasswordResetConfirmForm

def password_reset_confirm2(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid or expired token.')
        return redirect('password_reset_request2')

    if not reset_token.is_valid():
        messages.error(request, 'The token has expired. Please request a new password reset.')
        return redirect('password_reset_request2')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(reset_token.user, request.POST)
        if form.is_valid():
            form.save()
            reset_token.delete()  # Token used, now delete it
            return redirect('password_reset_complete')
        else:
            return render(request, 'password_reset_confirm2.html', {'form': form})
    else:
        form = PasswordResetConfirmForm(reset_token.user)
    
    return render(request, 'password_reset_confirm2.html', {'form': form})

def password_reset_complete(request):
    return render(request, 'password_reset_complete.html')
