from django.urls import path
from . import views

app_name = 'history'

urlpatterns = [
    path('', views.HistoryListView.as_view(), name='list'),
    path('search/', views.HistorySearchView.as_view(), name='search'),
    path('<uuid:id>/rerun/', views.HistoryRerunView.as_view(), name='rerun'),
    path('<uuid:id>/delete/', views.HistoryDeleteView.as_view(), name='delete'),
    path('clear/', views.HistoryClearView.as_view(), name='clear'),
]
