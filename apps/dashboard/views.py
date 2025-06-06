# apps/dashboard/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category
from django.contrib.auth.models import User

@staff_member_required
def dashboard_overview(request):
    """Main dashboard with key metrics"""
    
    # Calculate date ranges
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Revenue metrics
    total_revenue = Order.objects.filter(
        payment_status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        payment_status='completed',
        created_at__date__gte=last_30_days
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    weekly_revenue = Order.objects.filter(
        payment_status='completed',
        created_at__date__gte=last_7_days
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Order metrics
    total_orders = Order.objects.filter(payment_status='completed').count()
    monthly_orders = Order.objects.filter(
        payment_status='completed',
        created_at__date__gte=last_30_days
    ).count()
    
    pending_orders = Order.objects.filter(order_status='pending').count()
    
    # Product metrics
    total_products = Product.objects.filter(is_active=True).count()
    out_of_stock = Product.objects.filter(
        is_active=True,
        stock_quantity=0
    ).count()
    
    low_stock = Product.objects.filter(
        is_active=True,
        stock_quantity__lte=10,
        stock_quantity__gt=0
    ).count()
    
    # Customer metrics
    total_customers = User.objects.filter(is_active=True).count()
    new_customers = User.objects.filter(
        date_joined__date__gte=last_30_days
    ).count()
    
    # Average order value
    avg_order_value = Order.objects.filter(
        payment_status='completed'
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Recent orders
    recent_orders = Order.objects.filter(
        payment_status='completed'
    ).select_related('user').order_by('-created_at')[:10]
    
    context = {
        'revenue': {
            'total': total_revenue,
            'monthly': monthly_revenue,
            'weekly': weekly_revenue,
        },
        'orders': {
            'total': total_orders,
            'monthly': monthly_orders,
            'pending': pending_orders,
            'avg_value': avg_order_value,
        },
        'products': {
            'total': total_products,
            'out_of_stock': out_of_stock,
            'low_stock': low_stock,
        },
        'customers': {
            'total': total_customers,
            'new': new_customers,
        },
        'recent_orders': recent_orders,
    }
    
    return render(request, 'dashboard/overview.html', context)

@staff_member_required
def sales_analytics(request):
    """Sales analytics page"""
    return render(request, 'dashboard/analytics.html', {})

@staff_member_required
def inventory_management(request):
    """Inventory management page"""
    return render(request, 'dashboard/inventory.html', {})