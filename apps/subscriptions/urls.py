from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('pricing/', views.pricing_page_view, name='pricing'),
    path('api/pricing/', views.pricing_api_view, name='pricing_api'),
    path('api/usage/', views.usage_stats_view, name='usage_stats'),
    path('widget/', views.usage_widget_view, name='usage_widget'),
    path('checkout/<str:plan_name>/', views.create_checkout_session, name='checkout'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('success/', views.checkout_success, name='checkout_success'),
    path('cancel/', views.checkout_cancel, name='checkout_cancel'),

    path('manage/cancel/', views.cancel_subscription, name='cancel_subscription'),
]

