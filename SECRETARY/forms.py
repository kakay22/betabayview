from django import forms
from django.contrib.auth.hashers import make_password
from USERS.models import Resident

class ResidentForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = ['first_name', 'last_name', 'date_of_birth', 'age', 'email_address', 'contact_number', 'gender', 'relationship_to_household','occupation', 'household_representative']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type':'date'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'email_address': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'relationship_to_household': forms.Select(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'household_representative': forms.Select(attrs={'class': 'form-control'}),
        }