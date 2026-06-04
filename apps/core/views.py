from django.http import HttpResponse
from django.shortcuts import render


def health_check(request):
    return HttpResponse("OK", content_type="text/plain")


def home(request):
    """Root URL: guests get the marketing landing, authenticated users go
    straight to the app (the prompt composer)."""
    if request.user.is_authenticated:
        return render(request, 'pages/home.html')
    return render(request, 'pages/landing.html')


def app_composer(request):
    """The app entry point (prompt composer), reachable by everyone — the
    landing's 'Start free' CTA sends guests here (guest tier = a few free
    requests, no signup)."""
    return render(request, 'pages/home.html')
