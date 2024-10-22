# request_a_maintenance.py

from HOMEOWNER.models import Maintenance_request, Activitie
from django.contrib.auth.models import User
from .models import Log, Property
from SECRETARY.signals import create_maintenance_request_notification
from .signals import admin_create_maintenance_request_notification

def handle_maintenance_request(user_message, user_id, session):

    if 'request a maintenance' in user_message.lower() or 'request maintenance' in user_message.lower() or \
       'submit a maintenance request' in user_message.lower() or 'submit maintenance request' in user_message.lower():
        # Fetch user's active maintenance requests (pending or in-progress)
        pending_requests = Maintenance_request.objects.filter(name_of_owner__id=user_id, status='Pending')
        in_progress_requests = Maintenance_request.objects.filter(name_of_owner__id=user_id, status='In progress')
        done_requests = Maintenance_request.objects.filter(name_of_owner__id=user_id, status='Done')
        verified_requests = Maintenance_request.objects.filter(name_of_owner__id=user_id, status='verified')
        notverified_requests = Maintenance_request.objects.filter(name_of_owner__id=user_id, status='notverified')

        # Fetch user's total requests
        total_request = Maintenance_request.objects.filter(name_of_owner__id=user_id).count()
        # Count requests
        pending_count = pending_requests.count()
        in_progress_count = in_progress_requests.count()
        done_count = done_requests.count()
        verified_count = verified_requests.count()
        notverified_count = notverified_requests.count()

        # Prepare the bot's response
        response = f"""You currently have a total of {total_request} maintenance requests:
        • {pending_count} Pending
        • {in_progress_count} In progress
        • {done_count} Done
        • {verified_count} Verified
        • {notverified_count} Not Verified

        Would you like to request a maintenance? (Yes/No)
        """

        # Save the session state to track that the bot asked about maintenance
        session['maintenance_flow'] = 'request_confirm'
        session.save()

        return response

    # Check if we're in the middle of the maintenance request flow
    affirmative_responses = ['yes', 'correct', 'yeah', 'yep', 'sure', 'absolutely', 'definitely', 'certainly', 'of course']

    if session.get('maintenance_flow') == 'request_confirm':
        if any(response in user_message.lower() for response in affirmative_responses):
            # Fetch user's active maintenance requests (pending or in-progress)
            active_requests = Maintenance_request.objects.filter(name_of_owner__id=user_id)

            # Check if the user has 5 or more active requests
            if active_requests.count() >= 5:
                response = "Unfortunately, you have reached the maximum number of 5 maintenance requests per month. Please wait for one to be completed or you can delete some of your unwanted requests before requesting another."

                # Clear the session state
                session.pop('maintenance_flow', None)
                session.save()
                return response
            else:
                # Ask for the type of issue
                options = ['Plumbing', 'Electrical', 'Appliance Repair', 'Pest Control', 'Landscaping', 'HVAC']

                # Generate the numbered options
                numbered_options = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])

                # Build the response with the numbered options
                response = "Please choose one of the following options for maintenance:\n" + numbered_options + "\n\nYou can also type 'cancel' if you wish to cancel this request."


                # Update the session state
                session['maintenance_flow'] = 'choose_option'
                session.save()

                return response
        else:
            # End the flow if the user says no
            session.pop('maintenance_flow', None)
            session.save()

    ## Check if the user is choosing a maintenance option
    if session.get('maintenance_flow') == 'choose_option':
        options = ['Plumbing', 'Electrical', 'Appliance Repair', 'Pest Control', 'Landscaping', 'HVAC']

        # Generate numbered options
        numbered_options = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])

        # Check if the user wants to cancel the request
        if 'cancel' in user_message.lower():
            response = "Your maintenance request has been canceled. If you need assistance in the future, feel free to ask!"

            # Clear the session for the maintenance flow
            session.pop('selected_issue', None)
            session.pop('maintenance_flow', None)
            session.save()

            return response

        # Check if the user input is a number corresponding to an option
        if user_message.isdigit():
            selected_number = int(user_message)
            if 1 <= selected_number <= len(options):
                selected_option = options[selected_number - 1]
                
                # Store the selected option in the session
                session['selected_issue'] = selected_option

                # Ask for a description
                response = f"You've selected {selected_option}. Please provide a brief description of the issue.\n\nYou can also type 'cancel' if you wish to cancel this request."

                # Update the session state
                session['maintenance_flow'] = 'provide_description'
                session.save()

                return response
            else:
                response = "Invalid selection. Please choose a valid option by typing its number, or type 'cancel' to cancel the request."
                return response

        # Check if the user selected one of the valid maintenance options by name
        selected_option = next((option for option in options if option.lower() in user_message.lower()), None)

        if selected_option:
            # Store the selected option in the session
            session['selected_issue'] = selected_option

            # Ask for a description
            response = f"You've selected {selected_option}. Please provide a brief description of the issue.\n\nYou can also type 'cancel' if you wish to cancel this request."

            # Update the session state
            session['maintenance_flow'] = 'provide_description'
            session.save()

            return response
        else:
            # Show the numbered list of options
            response = f"I didn't quite understand that. Please choose one of the options below by typing its number or type 'cancel' to cancel the request:\n\n{numbered_options}"
            return response

    # Check if the user is providing the issue description
    if session.get('maintenance_flow') == 'provide_description':
        # Check if the user wants to cancel the request
        if user_message.lower() == 'cancel':
            response = "Your maintenance request has been canceled. If you need assistance in the future, feel free to ask!"

            # Clear the session state
            session.pop('selected_issue', None)
            session.pop('maintenance_flow', None)
            session.pop('issue_description', None)
            session.save()

            return response

        # Store the description in the session
        session['issue_description'] = user_message

        # Ask for the location of the issue
        response = "Thank you for the description. Could you please provide the location of the issue?\n\nYou can also type 'cancel' if you wish to cancel this request."

        # Update the session state
        session['maintenance_flow'] = 'provide_location'
        session.save()

        return response

    # Check if the user is providing the location of the issue
    if session.get('maintenance_flow') == 'provide_location':
        # Check if the user wants to cancel the request
        if 'cancel' in user_message.lower():
            response = "Your maintenance request has been canceled. If you need assistance in the future, feel free to ask!"

            # Clear the session for the maintenance flow
            session.pop('selected_issue', None)
            session.pop('issue_description', None)
            session.pop('maintenance_flow', None)
            session.save()

            return response

        # Retrieve the selected issue and description from the session
        selected_issue = session.get('selected_issue')
        issue_description = session.get('issue_description')

        # Create the maintenance request in the database
        owner = User.objects.get(id=user_id)
        owner_property = Property.objects.get(household_head=owner.homeowner)
        property_name = owner.homeowner.property.property_name
        
        maintenance_req = Maintenance_request.objects.create(
            name_of_owner=owner,
            type_of_issue=selected_issue,
            Description_of_issue=issue_description,
            location=user_message,
            status='Pending',  # Set the status to pending by default,
            property=owner_property,
        )

        # Log the request
        Log.objects.create(
            log_type='info',
            description=f"Homeowner '{owner.username}' requested maintenance: '{issue_description}' for property '{property_name}'.",
            user=owner
        )

        # Add an activity log
        Activitie.objects.create(
            name_of_owner=owner,
            name_of_activity='Requested a maintenance.'            
        )

        # Send notifications about the request
        create_maintenance_request_notification(maintenance_req)
        admin_create_maintenance_request_notification(maintenance_req)

        # Confirm the request has been submitted
        response = (
            f"Your maintenance request has been submitted successfully!\n\n"
            f"Maintenance Details:\n"
            f"• Type of Issue: {selected_issue}\n"
            f"• Description: {issue_description}\n"
            f"• Location: {user_message}\n"
            f"• Status: Pending\n"
            f"\nThank you for your request! We will address it as soon as possible."
        )

        # Clear the session state after the request is completed
        session.pop('maintenance_flow', None)
        session.pop('selected_issue', None)
        session.pop('issue_description', None)
        session.save()

        return response
