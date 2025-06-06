# apps/dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_overview, name='overview'),
    path('analytics/', views.sales_analytics, name='analytics'),
    path('inventory/', views.inventory_management, name='inventory'),
]