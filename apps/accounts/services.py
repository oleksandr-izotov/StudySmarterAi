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
    now = timezone.now()

    # Atomically claim the token: a single UPDATE flips is_used False->True only
    # if it's still unused and unexpired. Exactly one concurrent request gets
    # rowcount==1, so a link can never be redeemed twice (the previous
    # check-then-save was a race).
    claimed = MagicLinkToken.objects.filter(
        token=token_str, is_used=False, expires_at__gt=now
    ).update(is_used=True)

    if not claimed:
        if not MagicLinkToken.objects.filter(token=token_str).exists():
            return None, "Invalid token"
        return None, "Token expired or already used"

    token_obj = MagicLinkToken.objects.get(token=token_str)
    email = token_obj.email

    # A magic link proves control of the inbox, so it should log into the
    # EXISTING account for that email (incl. password accounts), not spawn a
    # parallel account keyed on username==email. Match by email first.
    user = User.objects.filter(email__iexact=email).order_by('id').first()

    if user is None:
        from .models import UserProfile
        # New magic-link-only account. Prefer email as username, but never
        # collide with an existing username.
        username = email
        if User.objects.filter(username=username).exists():
            base, suffix = email, 1
            while User.objects.filter(username=username).exists():
                username = f"{base}+{suffix}"
                suffix += 1
        user = User.objects.create_user(username=username, email=email)
        UserProfile.objects.create(user=user)

    return user, None
