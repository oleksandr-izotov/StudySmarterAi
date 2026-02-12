from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class LoginForm(AuthenticationForm):
    pass

class ProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['language', 'tone', 'depth', 'format', 'goal']

class MagicLinkRequestForm(forms.Form):
    email = forms.EmailField(label="Email address", required=True)

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email']
