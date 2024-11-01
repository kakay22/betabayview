from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from HOMEOWNER.models import HomeOwner
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here
class Secretary(models.Model):
	gender_choices = [
		('male', 'Male'),
		('female', 'Female'),
	]

	relationship_choices = [
		('mother', 'Mother'),
		('father', 'Father'),
		('son', 'Son'),
		('daugter', 'Daughter'),
		('others', 'Others'),
	]

	educational_choices = [
		('elementary' ,'Elementary'),
		('highschool' ,'Highschool'),
		('college' ,'College'),
	]

	user = models.OneToOneField(User, on_delete=models.CASCADE)
	role = models.CharField(max_length=255, default='secretary')
	first_name = models.CharField(max_length=255)
	last_name = models.CharField(max_length=255)
	date_of_birth = models.DateField()
	age = models.IntegerField(default=0)
	gender = models.CharField(max_length=255, choices=gender_choices)
	contact_number = models.IntegerField()
	email_address = models.CharField(max_length=255)
	name_of_emergency_contact = models.CharField(max_length=255)
	relationship_to_secretary = models.CharField(max_length=255, choices=relationship_choices)
	emergency_contact_number = models.IntegerField()
	highest_educational_attainment = models.CharField(max_length=255, choices=educational_choices)
	user_name = models.CharField(max_length=255)
	password = models.CharField(max_length=128)
	profile_picture = models.ImageField(default='secretary.png')

	def set_password(self, raw_password):
		self.password = make_password(raw_password)
		self.save()

	def check_password(self, raw_password):
		return check_password(raw_password, self.password)

	def __str__(self):
		return self.user_name

	class Meta:
		verbose_name_plural = 'Secretaries'


class Event(models.Model):
	event_name = models.CharField(max_length=255)
	event_description = models.TextField()
	event_date = models.DateField()
	event_time = models.TimeField()
	date_created = models.DateField(auto_now_add=True)
	location = models.CharField(max_length=255)
	image = models.ImageField(default='events.jpg')

	def __str__(self):
		return self.event_name


class Comment(models.Model):
	owner_commentor = models.ForeignKey(User, on_delete=models.CASCADE)
	event = models.ForeignKey(Event, on_delete=models.CASCADE)
	comment = models.TextField()
	date_commented = models.DateTimeField(auto_now_add=True)
	image = models.ImageField(default='events.jpg')

	def __str__(self):
		return self.comment


class Message(models.Model):
	message = models.TextField()
	sender = models.CharField(max_length=255)
	sent_time = models.DateTimeField(auto_now_add=True)
	is_read = models.BooleanField(default=False)
	

	def __str__(self):
		return self.sender


class NonSuperUserManager(models.Manager):
		def get_queryset(self):
			return super().get_queryset().filter(is_superuser=False)
		
class NonSuperUser(User):
	objects = NonSuperUserManager()
	class Meta:
		proxy = True

class PropertyModel(models.Model):
    model_name = models.CharField(max_length=300)

    def __str__(self):
        return self.model_name

	
class Property(models.Model):
    BLOCK_CHOICES = [(i, i) for i in range(1, 21)]
    HOUSE_CHOICES = [(i, i) for i in range(1, 21)]

    description = (
		('single', 'Single'),
		('double', 'Double'),
		('family', 'Family'),
	)
    availability_choices = (
		('available', 'Available'),
		('occupied', 'Occupied'),
		('under_maintenance', 'Under maintenance'),
	)

	#household information
    household_head = models.OneToOneField(HomeOwner, null=True, blank=True, on_delete=models.SET_NULL, related_name='household_head')
    property_name = models.CharField(max_length=255)
    property_model = models.CharField(max_length=255, null=True, blank=True)
    contact_no = models.IntegerField(null=True, blank=True)
    photo = models.ImageField(default="pope-francis-village.png")
    # Dropdown for block number
    property_block_no = models.PositiveSmallIntegerField(choices=BLOCK_CHOICES)
    # Dropdown for house number, with unique constraint
    property_house_no = models.PositiveSmallIntegerField(choices=HOUSE_CHOICES, unique=True)
    lot_size = models.DecimalField(max_digits=10, decimal_places=2)
    property_description = models.CharField(max_length=255, choices=description)
    bathroom = models.IntegerField()
    bedroom = models.IntegerField()
    availability = models.CharField(max_length=255, choices=availability_choices, default="available")
    date_registered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.property_name
	
    class Meta:
        verbose_name_plural = 'Properties'

# New model to handle multiple images
class PropertyImage(models.Model):
    property = models.ForeignKey(Property, related_name='images', on_delete=models.CASCADE)
    interrior_image = models.ImageField(upload_to='property_images/', null=True, blank=True)
    exterrior_image = models.ImageField(upload_to='property_images/', null=True, blank=True)

    def __str__(self):
        return f"Image for {self.property.property_name}"

class MaintenancePersonnel(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('ongoing', 'Ongoing Repair'),
    ]

    ROLE_CHOICES = [
    ('appliance repair technician', 'Appliance Repair'),
    ('landscaper', 'Landscaper'),
    ('pest control technician', 'Pest Control Technician'),
    ('hvac technician', 'HVAC Technician'),
    ('carpenter', 'Carpenter'),
    ('plumber', 'Plumber'),
    ('electrician', 'Electrician'),
]

    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    location = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    image = models.ImageField(default='repairmane.jpg')
    date_registered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.role}"


class AdminNotification(models.Model):
    ICON_CHOICES = [
        ('info', 'bi-info-circle'),
        ('pending_account', 'bi-person-badge'),
        ('maintenance', 'bi-wrench'),
        # Add more icon choices as needed
    ]

    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='info')  # New icon field

    def __str__(self):
        return self.message

class Log(models.Model):
    LOG_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]

    # Basic information fields
    timestamp = models.DateTimeField(default=timezone.now)  # When the log entry was created
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)  # Type of log (info, warning, etc.)
    description = models.TextField()  # Detailed message about the log entry
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # User associated with the log

    # Optional: Action taken, if applicable
    action = models.CharField(max_length=255, null=True, blank=True)  # What action was taken

    def __str__(self):
        return f"{self.timestamp} - {self.log_type}: {self.description}"

    class Meta:
        ordering = ['-timestamp']  # Order logs by most recent first


class Announcement(models.Model):
    # ForeignKey to User model for the creator of the announcement
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    
    # Title of the announcement
    title = models.CharField(max_length=255)
    
    # Content of the announcement
    content = models.TextField()
    
    # Date when the announcement was created
    created_at = models.DateTimeField(default=timezone.now)
    
    # Date when the announcement is set to expire (optional)
    expiration_date = models.DateTimeField(null=True, blank=True)
    
    # Boolean to indicate if the announcement is active or not
    is_active = models.BooleanField(default=True)

	# Profile picture of the user creating the announcement
    profile_picture = models.ImageField(default='admin.png')

    def __str__(self):
        return self.title
	
class AnnouncementComment(models.Model):
    announcement = models.ForeignKey(Announcement, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    profile = models.ImageField(null=True, blank=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.announcement.title}"
	
class PaymentReminder(models.Model):
    homeowner = models.ForeignKey(HomeOwner, on_delete=models.CASCADE, related_name='payment_reminders')
    subject = models.CharField(max_length=255, blank=True, null=True)
    amount = models.IntegerField()
    due_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_reminders')

    def __str__(self):
        return f'Reminder for {self.homeowner.user.username} - {self.subject}'

class Feedback(models.Model):
    FEEDBACK_TYPES = [
        ('Feature Request', 'Feature Request'),
        ('Bug Report', 'Bug Report'),
        ('General Feedback', 'General Feedback'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Optional, if you want to link to a user
    feedback_type = models.CharField(max_length=50, choices=FEEDBACK_TYPES)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    contact_info = models.CharField(max_length=255, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.feedback_type}"

class ChatbotResponse(models.Model):
    user_query = models.CharField(max_length=255)  # Store user queries
    bot_response = models.TextField()  # Store bot responses

    def __str__(self):
        return f"Query: {self.user_query} | Response: {self.bot_response}"


class ChatConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    user_message = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    likes = models.PositiveIntegerField(default=0, null=True, blank=True)
    dislikes = models.PositiveIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return f"Conversation with {self.user} at {self.timestamp}"

class ChatFeedback(models.Model):
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE)
    feedback_type = models.CharField(max_length=10, choices=[('like', 'Like'), ('dislike', 'Dislike')])
    timestamp = models.DateTimeField(auto_now_add=True)


class ChatHistoryMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sender = models.CharField(max_length=10)  # 'user' or 'bot'
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.sender}: {self.message}'
    

class VisitRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]

    visitor_full_name = models.CharField(max_length=255)
    visitor_relation = models.CharField(max_length=100)
    visit_date = models.DateTimeField()
    purpose = models.TextField()
    household_head = models.ForeignKey(HomeOwner, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # Latitude field
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # Longitude field
    

    def __str__(self):
        return f"{self.visitor_full_name} - {self.visit_date.strftime('%Y-%m-%d %H:%M')}"