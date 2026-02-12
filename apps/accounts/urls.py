from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('magic-link/', views.MagicLinkRequestView.as_view(), name='magic_link_request'),
    path('magic-link/verify/<uuid:token>/', views.MagicLinkVerifyView.as_view(), name='magic_link_verify'),
    path('account/', views.AccountView.as_view(), name='account'),
]
