from functools import wraps
from django.http import JsonResponse
from .services import UsageService, SubscriptionService


def check_rate_limit(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        session_key = request.session.session_key
        
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        if not UsageService.can_make_request(request.user, session_key):
            plan = SubscriptionService.get_user_plan(request.user, session_key)
            is_guest = not request.user.is_authenticated
            
            response_data = {
                'error': 'rate_limit_exceeded',
                'is_guest': is_guest,
                'plan': plan.display_name if plan else 'Unknown',
                'limit': plan.limit_count if plan else 0,
                'period': plan.limit_period if plan else 'day',
            }
            
            if request.headers.get('HX-Request'):
                from django.template.loader import render_to_string
                from django.http import HttpResponse
                html = render_to_string('partials/rate_limit_exceeded.html', {
                    'is_guest': is_guest,
                    'plan': plan,
                    'stats': UsageService.get_usage_stats(request.user, session_key),
                }, request=request)
                return HttpResponse(html, status=429)
            
            return JsonResponse(response_data, status=429)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_subscription(plan_names):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            plan = SubscriptionService.get_user_plan(
                request.user,
                request.session.session_key
            )
            
            if plan is None or plan.name not in plan_names:
                return JsonResponse({
                    'error': 'subscription_required',
                    'required_plans': plan_names,
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
