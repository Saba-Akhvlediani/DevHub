from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class UserRegistrationForm(forms.Form):
    """User registration form"""
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': 'You must accept the terms and conditions.'
        }
    )
    
    def clean_username(self):
        username = self.cleaned_data['username']
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        
        # Username validation
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Username can only contain letters, numbers, and underscores.')
        
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        
        # Email validation
        if '@' not in email:
            raise ValidationError('Email must contain @ symbol.')
        
        return email
    
    def clean_password(self):
        password = self.cleaned_data['password']
        
        # Password validation
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must contain at least one number.')
        
        if not re.search(r'[!?.,>]', password):
            raise ValidationError('Password must contain at least one special character (!, ?, ., ,, >).')
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Passwords do not match.')
        
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """User profile editing form"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Check if email already exists (excluding current user)
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('An account with this email already exists.')
        
        return email