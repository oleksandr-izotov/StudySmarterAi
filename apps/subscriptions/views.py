from django.http import JsonResponse
from django.shortcuts import render
from .models import SubscriptionPlan
from .services import UsageService, SubscriptionService


def pricing_page_view(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')
    current_plan = SubscriptionService.get_user_plan(
        request.user,
        request.session.session_key
    )
    
    plans_with_current = []
    
    # Custom translations for plan names
    from django.utils.translation import gettext as _
    
    for plan in plans:
        display_name = plan.display_name
        if plan.name == 'guest':
            display_name = _('Guest')
        elif plan.name == 'free':
            display_name = _('Free')
        elif plan.name == 'pro':
            display_name = _('Pro')
        elif plan.name == 'pro_plus':
            display_name = _('Pro Plus')
            
        plans_with_current.append({
            'name': plan.name,
            'display_name': display_name,
            'limit_count': plan.limit_count,
            'limit_period': plan.limit_period,
            'monthly_price': plan.monthly_price,
            'is_paid': plan.is_paid,
            'is_current': current_plan and current_plan.id == plan.id,
        })
    
    return render(request, 'pages/pricing.html', {
        'plans': plans_with_current,
        'current_plan': current_plan,
    })


def pricing_api_view(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')
    current_plan = SubscriptionService.get_user_plan(
        request.user,
        request.session.session_key
    )
    
    plans_data = []
    for plan in plans:
        plans_data.append({
            'name': plan.name,
            'display_name': plan.display_name,
            'limit_count': plan.limit_count,
            'limit_period': plan.limit_period,
            'monthly_price': float(plan.monthly_price),
            'is_paid': plan.is_paid,
            'is_current': current_plan and current_plan.id == plan.id,
        })
    
    return JsonResponse({
        'plans': plans_data,
        'current_plan': current_plan.name if current_plan else None,
    })


def usage_stats_view(request):
    session_key = request.session.session_key
    
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    stats = UsageService.get_usage_stats(request.user, session_key)
    
    return JsonResponse({
        'plan': stats['plan'].display_name if stats['plan'] else None,
        'used': stats['used'],
        'limit': stats['limit'],
        'remaining': stats['remaining'],
        'period': stats['period'],
        'is_unlimited': stats.get('is_unlimited', False),
    })


def usage_widget_view(request):
    """HTMX endpoint to refresh usage widget."""
    return render(request, 'partials/usage_widget.html')


import stripe
import json
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .stripe_service import StripeService


@login_required
@require_POST
def create_checkout_session(request, plan_name):
    plan = get_object_or_404(SubscriptionPlan, name=plan_name, is_active=True, is_paid=True)

    if not plan.stripe_price_id:
        return JsonResponse({'error': 'Plan not configured for payments'}, status=400)

    # Build URLs with correct host (includes port)
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()  # includes port if non-standard
    base_url = f"{scheme}://{host}"
    success_url = f"{base_url}/subscriptions/success/"
    cancel_url = f"{base_url}/subscriptions/cancel/"

    try:
        checkout_url = StripeService.create_checkout_session(
            user=request.user,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url
        )
        return redirect(checkout_url)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse('Invalid payload', status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse('Invalid signature', status=400)

    event_id = event['id']
    event_type = event['type']

    if StripeService.is_event_processed(event_id):
        return HttpResponse('Already processed', status=200)

    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        StripeService.handle_checkout_completed(session)

    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        StripeService.handle_subscription_updated(subscription)

    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        StripeService.handle_subscription_deleted(subscription)

    StripeService.mark_event_processed(event_id, event_type, event['data']['object'])

    return HttpResponse('OK', status=200)


@login_required
def checkout_success(request):
    session_id = request.GET.get('session_id')

    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            session_user_id = session.get('metadata', {}).get('user_id')
            if session_user_id == str(request.user.id):
                if session.get('payment_status') == 'paid':
                    StripeService.handle_checkout_completed(session)
        except stripe.error.StripeError:
            pass

    return render(request, 'pages/checkout_success.html')


@login_required
def checkout_cancel(request):
    return render(request, 'pages/checkout_cancel.html')


@login_required
@require_POST
def cancel_subscription(request):
    success = StripeService.cancel_subscription(request.user)
    if success:
        return redirect('account')
    return JsonResponse({'error': 'Could not cancel subscription'}, status=400)

