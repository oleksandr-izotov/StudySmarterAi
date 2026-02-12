from django.urls import path
from . import views

urlpatterns = [
    path('', views.prompt_create_view, name='prompt_create'),
    path('<uuid:id>/', views.prompt_detail_view, name='prompt_detail'),
    path('<uuid:id>/sections/<str:type>/', views.section_detail_view, name='section_detail'),
    path('<uuid:id>/sections/<str:type>/regenerate/', views.section_regenerate_view, name='section_regenerate'),
]
