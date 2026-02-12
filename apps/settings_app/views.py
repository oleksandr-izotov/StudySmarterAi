from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from apps.accounts.models import UserProfile
from django.utils.translation import gettext_lazy as _
from apps.core.utils import get_user_settings

class SettingsView(View):
    template_name = 'pages/settings.html'

    def get(self, request):
        settings = get_user_settings(request)
        return render(request, self.template_name, {'settings': settings})

    def post(self, request):
        # 2. Get data from form
        language = request.POST.get('language')
        tone = request.POST.get('tone')
        depth = request.POST.get('depth')
        
        # 3. Save Settings
        if request.user.is_authenticated:
            # Update Profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.language = language
            profile.tone = tone
            profile.depth = depth
            profile.save()
            
            # Update session too for consistency if mixed usage occurs
            request.session['language'] = language
            request.session['tone'] = tone
            request.session['depth'] = depth
        else:
            # Save to Session
            request.session['language'] = language
            request.session['tone'] = tone
            request.session['depth'] = depth
        
        messages.success(request, _('Настройки сохранены'))
        
        # If HTMX request, return the form partial with updated values
        if request.headers.get('HX-Request'):
             return render(request, 'partials/settings_form.html', {
                 'settings': {'language': language, 'tone': tone, 'depth': depth}
             })

        return redirect('settings:index')
