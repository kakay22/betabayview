from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class HomeOwner(models.Model):
	gender_choices = [
		('male', 'Male'),
		('female', 'Female'),
	]

	yesno_choices = [
		('yes', 'Yes'),
		('no', 'No'),
	]

	c_status = [
		('single', 'Single'),
		('maried', 'Maried'),
		('divorced', 'Divorced'),
		('widowed', 'Widowed'),
	]

	religion_choices = [
		('roman catholic', 'Roman catholic'),
		('Iglesia ni cristo', 'Iglesia ni cristo'),
		('christian', 'Christian'),
		('born again', 'Born again'),
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
	property = models.ForeignKey('ADMIN.property', on_delete=models.CASCADE, blank=True, null=True)
	role = models.CharField(max_length=255, default='owner')
	#middle_name = models.CharField(max_length=255, null=True, blank=True)
	#suffix = models.CharField(max_length=255, null=True, blank=True)
	date_of_birth = models.DateField(null=True, blank=True)
	age = models.IntegerField(null=True, blank=True, default=0)
	contact_number = models.IntegerField(null=True, blank=True, default=0)
	#sr_citizen = models.CharField(max_length=100, choices=yesno_choices, null=True, blank=True)
	gender = models.CharField(max_length=200, choices=gender_choices, null=True, blank=True)
	#place_of_birth = models.CharField(max_length=255, null=True, blank=True)
	#civil_status = models.CharField(max_length=255, choices=c_status, null=True, blank=True)
	#religion = models.CharField(max_length=255, choices=religion_choices, null=True, blank=True)
	#pwd = models.CharField(max_length=255, choices=yesno_choices, null=True, blank=True)
	#pregnant = models.CharField(max_length=255, choices=yesno_choices, null=True, blank=True)
	relationship_to_household = models.CharField(max_length=255, choices=relationship_choices, null=True, blank=True)
	#previous_address = models.CharField(max_length=255, null=True, blank=True)
	#highest_educational_attainment = models.CharField(max_length=255, choices=educational_choices, null=True, blank=True)
	occupation = models.CharField(max_length=255, null=True, blank=True)
	registration_date = models.DateField(auto_now_add=True)
	block_number = models.IntegerField(null=True, blank=True)
	house_number = models.IntegerField(null=True, blank=True)
	total_household_members = models.IntegerField(null=True, blank=True)
	profile_picture = models.ImageField(default='homeOwner.png')
	pending = models.BooleanField(default=True)

	def __str__(self):
		return self.user.username


class Resident(models.Model):
	gender_choices = [
		('male', 'Male'),
		('female', 'Female'),
	]

	yesno_choices = [
		('yes', 'Yes'),
		('no', 'No'),
	]

	c_status = [
		('single', 'Single'),
		('maried', 'Maried'),
		('divorced', 'Divorced'),
		('widowed', 'Widowed'),
	]

	religion_choices = [
		('roman catholic', 'Roman catholic'),
		('Iglesia ni cristo', 'Iglesia ni cristo'),
		('christian', 'Christian'),
		('born again', 'Born again'),
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

	first_name = models.CharField(max_length=255)
	#middle_name = models.CharField(max_length=255)
	last_name = models.CharField(max_length=255)
	#suffix = models.CharField(max_length=255)
	date_of_birth = models.DateField()
	age = models.IntegerField()
	email_address = models.EmailField(max_length=255, unique=True)
	contact_number = models.IntegerField()
	#sr_citizen = models.CharField(max_length=100, choices=yesno_choices)
	gender = models.CharField(max_length=200, choices=gender_choices)
	#place_of_birth = models.CharField(max_length=255)
	#civil_status = models.CharField(max_length=255, choices=c_status)
	#religion = models.CharField(max_length=255, choices=religion_choices)
	#pwd = models.CharField(max_length=255, choices=yesno_choices)
	#pregnant = models.CharField(max_length=255, choices=yesno_choices)
	relationship_to_household = models.CharField(max_length=255, choices=relationship_choices)
	#previous_address = models.CharField(max_length=255)
	#highest_educational_attainment = models.CharField(max_length=255, choices=educational_choices)
	occupation = models.CharField(max_length=255)
	#registration_date = models.DateField()
	block_number = models.IntegerField(null=True, blank=True)
	lot_number = models.IntegerField(null=True, blank=True)
	household_representative = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)

	def __str__(self):
		return self.first_name

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() - self.created_at < timezone.timedelta(hours=24)