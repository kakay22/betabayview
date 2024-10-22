# forms.py
from django import forms
from django.contrib.auth.hashers import make_password
from .models import HomeOwner
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from django.contrib.auth.forms import PasswordChangeForm

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')

    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        
        # Add 'form-control' class and set required attribute for each field
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'required': 'required',  # Marking as required
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'required': 'required',  # Marking as required
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'required': 'required',  # Marking as required
        })

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password1", "password2"]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'maxlength': '10',
                'required': 'required',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'required': 'required',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                
                'required': 'required',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                
                'required': 'required',
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-1 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Password',
                'required': 'required'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-1 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Confirm Password',
                'required': 'required',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password')
        password2 = cleaned_data.get("password_confirm")

        if password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email is already in use
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")
        return email

class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'}),
            'last_name': forms.TextInput(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'}),
            'username': forms.TextInput(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'}),
            'email': forms.EmailInput(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'}),
        }
    
class HomeOwnerForm(forms.ModelForm):
    class Meta:
        model = HomeOwner
        fields = ['date_of_birth', 'age', 'contact_number', 'gender', 'relationship_to_household', 'occupation','profile_picture']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', 'type':'date', 'require': True, 'required': 'required',}),
            'age': forms.NumberInput(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', 'require': True }),
            'contact_number': forms.NumberInput(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', 'require': True, 'required': 'required',}),
            'gender': forms.Select(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', 'require': True}),
            'relationship_to_household': forms.Select(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', 'require': True, 'required': 'required',}),
            'occupation': forms.TextInput(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', 'require': True, 'required': 'required',}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already taken.')

        return cleaned_data

class OwnerLoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password',
    }))

    def add_error(self, field, error):
        if field:
            super().add_error(field, error)
        else:
            self._errors[forms.forms.NON_FIELD_ERRORS] = self.error_class([error])

class SecretaryLoginForm(forms.Form):
    user_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password',
    }))

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Enter your registered email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control border py-[.80rem] border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400',
            'placeholder': 'example@domain.com',  # Placeholder text
        })
    )

class PasswordResetConfirmForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']

    def __init__(self, *args, **kwargs):
        super(PasswordResetConfirmForm, self).__init__(*args, **kwargs)
        
        # Add Tailwind CSS classes to the password fields
        self.fields['new_password1'].widget.attrs.update({
            'class': 'block w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring focus:ring-blue-500',
            'placeholder': 'Enter your new password',
        })
        
        self.fields['new_password2'].widget.attrs.update({
            'class': 'block w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring focus:ring-blue-500',
            'placeholder': 'Confirm your new password',
        })

    def clean_new_password2(self):
        # Custom validation to ensure passwords match
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("The two password fields didn't match.")

        return new_password2


