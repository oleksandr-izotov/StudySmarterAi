from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from .models import MagicLinkToken
from django.contrib.auth.models import User

def create_magic_link(email):
    # Expire in 15 minutes
    expires_at = timezone.now() + timedelta(minutes=15)
    token_obj = MagicLinkToken.objects.create(email=email, expires_at=expires_at)
    return token_obj

def send_magic_link_email(token_obj, request):
    verify_url = reverse('magic_link_verify', kwargs={'token': str(token_obj.token)})
    full_link = request.build_absolute_uri(verify_url)
    
    subject = "Your Login Link for Study Smart"
    message = f"Click the link to log in: {full_link}\n\nThis link is valid for 15 minutes."
    
    # In a real app, use a task queue like Celery. 
    # For now, synchronous sending (or console output if configured).
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@studysmart.local',
        [token_obj.email],
        fail_silently=False,
    )

    # For local development convenience, print the link directly to console to avoid auto-formatting issues
    if settings.DEBUG:
        print(f"\n\n--- MAGIC LINK ---\n{full_link}\n------------------\n\n")

def get_user_from_token(token_str):
    try:
        token_obj = MagicLinkToken.objects.get(token=token_str)
    except MagicLinkToken.DoesNotExist:
        return None, "Invalid token"

    if not token_obj.is_valid():
        return None, "Token expired or already used"

    # Mark as used
    token_obj.is_used = True
    token_obj.save()

    # Get or create user
    user, created = User.objects.get_or_create(username=token_obj.email, defaults={'email': token_obj.email})
    
    if created:
        from .models import UserProfile
        UserProfile.objects.create(user=user)

    return user, None
