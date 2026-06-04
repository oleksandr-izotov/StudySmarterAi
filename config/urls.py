"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from apps.core.views import health_check, home, app_composer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.accounts.urls')),
    path('prompts/', include('apps.prompts.urls')),
    path('history/', include('apps.history.urls')),
    path('settings/', include('apps.settings_app.urls')),
    path('subscriptions/', include('apps.subscriptions.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('health/', health_check, name='health_check'),
    path('agreement/', TemplateView.as_view(template_name='pages/agreement.html'), name='agreement'),
    path('contacts/', TemplateView.as_view(template_name='pages/contacts.html'), name='contacts'),
    path('features/', TemplateView.as_view(template_name='pages/features.html'), name='features'),
    path('start/', app_composer, name='app'),
    path('', home, name='home'),
]
