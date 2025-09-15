from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, LecturerProfile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    registration_number = forms.CharField(max_length=20, required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 
                 'registration_number', 'phone_number', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.registration_number = self.cleaned_data['registration_number']
        user.phone_number = self.cleaned_data['phone_number']
        
        if commit:
            user.save()
            
            # Create profile based on role
            if user.role == 'student':
                StudentProfile.objects.create(user=user)
            elif user.role == 'lecturer':
                LecturerProfile.objects.create(user=user)
                
        return user