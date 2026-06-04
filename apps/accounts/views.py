from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views import View
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .forms import UserRegistrationForm, LoginForm, MagicLinkRequestForm, ProfileSettingsForm
from .services import create_magic_link, send_magic_link_email, get_user_from_token
from .models import UserProfile

class RegisterView(View):
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'auth/register.html', {'form': form})

    @method_decorator(ratelimit(key='ip', rate='10/h', block=True))
    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('home') # Assuming 'home' url exists
        return render(request, 'auth/register.html', {'form': form})

class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'auth/login.html', {'form': form})

    @method_decorator(ratelimit(key='ip', rate='10/m', block=True))
    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        return render(request, 'auth/login.html', {'form': form})

class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('login')

class MagicLinkRequestView(View):
    def get(self, request):
        form = MagicLinkRequestForm()
        return render(request, 'auth/magic_link.html', {'form': form})

    @method_decorator(ratelimit(key='ip', rate='5/h', block=True))
    def post(self, request):
        form = MagicLinkRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            token_obj = create_magic_link(email)
            send_magic_link_email(token_obj, request)
            messages.success(request, "Magic link sent! Check your email.")
            return redirect('magic_link_request')
        return render(request, 'auth/magic_link.html', {'form': form})

class MagicLinkVerifyView(View):
    def get(self, request, token):
        user, error = get_user_from_token(token)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, error)
            return redirect('login')

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import UserUpdateForm

@method_decorator(login_required, name='dispatch')
class AccountView(View):
    template_name = 'pages/account.html'

    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        return render(request, self.template_name, {
            'user_form': user_form,
            'password_form': password_form
        })

    def post(self, request):
        if 'change_password' in request.POST:
            user_form = UserUpdateForm(instance=request.user)
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль успешно изменен.')
                return redirect('account')
            else:
                 messages.error(request, 'Ошибка при смене пароля.')
        else:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            password_form = PasswordChangeForm(user=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Данные аккаунта обновлены.')
                return redirect('account')
            else:
                 messages.error(request, 'Ошибка при обновлении данных.')

        return render(request, self.template_name, {
            'user_form': user_form,
            'password_form': password_form
        })


