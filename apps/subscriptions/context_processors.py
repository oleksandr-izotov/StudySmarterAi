from django.utils.translation import gettext_lazy as _, gettext
from .services import UsageService, SubscriptionService


# Mapping of plan display names to translatable strings
PLAN_NAME_TRANSLATIONS = {
    'Guest': _('Guest'),
    'Free': _('Free'),
    'Pro': _('Pro'),
    'Pro+': _('Pro+'),
}


def get_translated_plan_name(plan):
    """Get translated plan name from database display_name."""
    if not plan:
        return gettext('Guest')
    display_name = plan.display_name
    # If we have a translation, use it; otherwise return as-is
    if display_name in PLAN_NAME_TRANSLATIONS:
        return gettext(display_name)
    return display_name


def usage_stats(request):
    session_key = request.session.session_key
    
    if not session_key and not request.user.is_authenticated:
        if hasattr(request, 'session'):
            request.session.create()
            session_key = request.session.session_key
    
    stats = UsageService.get_usage_stats(request.user, session_key)
    plan = SubscriptionService.get_user_plan(request.user, session_key)
    
    if stats['limit'] and stats['limit'] > 0:
        usage_percent = int((stats['used'] / stats['limit']) * 100)
    else:
        usage_percent = 0
    
    if usage_percent < 50:
        usage_color = 'green'
    elif usage_percent < 80:
        usage_color = 'yellow'
    else:
        usage_color = 'red'
    
    return {
        'usage_stats': {
            'plan': plan,
            'plan_name': get_translated_plan_name(plan),
            'used': stats['used'],
            'limit': stats['limit'],
            'remaining': stats['remaining'],
            'period': stats['period'],
            'is_unlimited': stats.get('is_unlimited', False),
            'percent': usage_percent,
            'color': usage_color,
            'is_guest': not request.user.is_authenticated,
        }
    }
