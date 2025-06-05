from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'full_billing_name', 'email', 'total_amount', 
        'order_status', 'payment_status', 'created_at'
    ]
    list_filter = ['order_status', 'payment_status', 'created_at', 'updated_at']
    search_fields = ['order_number', 'email', 'billing_first_name', 'billing_last_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'email', 'order_status', 'payment_status')
        }),
        ('Billing Information', {
            'fields': (
                'billing_first_name', 'billing_last_name', 'billing_company',
                'billing_address', 'billing_city', 'billing_postal_code', 
                'billing_country', 'billing_phone'
            )
        }),
        ('Shipping Information', {
            'fields': (
                'different_shipping', 'shipping_first_name', 'shipping_last_name',
                'shipping_company', 'shipping_address', 'shipping_city',
                'shipping_postal_code', 'shipping_country', 'shipping_phone'
            ),
            'classes': ('collapse',)
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'total_amount')
        }),
        ('Notes', {
            'fields': ('order_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'price', 'total_price']
    list_filter = ['order__created_at']
    search_fields = ['order__order_number', 'product_name', 'product_model']
    readonly_fields = ['total_price']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'payment_method', 'amount', 'status', 
        'card_last_four', 'transaction_id', 'created_at'
    ]
    list_filter = ['payment_method', 'status', 'created_at', 'processed_at']
    search_fields = ['order__order_number', 'transaction_id', 'card_last_four']
    readonly_fields = ['created_at', 'processed_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'payment_method', 'amount', 'currency', 'status')
        }),
        ('Card Information', {
            'fields': ('card_last_four', 'card_brand')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at')
        }),
    )