from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment/<int:order_id>/', views.payment_view, name='payment'),
    path('payment-failed/<int:order_id>/', views.payment_failed_view, name='payment_failed'),
    path('success/<int:order_id>/', views.order_success_view, name='order_success'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
]