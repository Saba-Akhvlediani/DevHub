from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from apps.products.models import Product
import uuid


class Order(models.Model):
    """Customer orders"""
    ORDER_STATUS_CHOICES = [
        ('pending', _('Pending Payment')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]

    # Order identification
    order_number = models.CharField(max_length=32, unique=True, verbose_name=_("Order Number"))
    
    # Customer information
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("User"))
    email = models.EmailField(verbose_name=_("Email"))
    
    # Billing information
    billing_first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    billing_last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))
    billing_company = models.CharField(max_length=100, blank=True, verbose_name=_("Company"))
    billing_address = models.TextField(verbose_name=_("Address"))
    billing_city = models.CharField(max_length=100, verbose_name=_("City"))
    billing_postal_code = models.CharField(max_length=20, verbose_name=_("Postal Code"))
    billing_country = models.CharField(max_length=100, default="Georgia", verbose_name=_("Country"))
    billing_phone = models.CharField(max_length=20, verbose_name=_("Phone"))
    
    # Shipping information
    different_shipping = models.BooleanField(default=False, verbose_name=_("Different Shipping Address"))
    shipping_first_name = models.CharField(max_length=100, blank=True, verbose_name=_("Shipping First Name"))
    shipping_last_name = models.CharField(max_length=100, blank=True, verbose_name=_("Shipping Last Name"))
    shipping_company = models.CharField(max_length=100, blank=True, verbose_name=_("Shipping Company"))
    shipping_address = models.TextField(blank=True, verbose_name=_("Shipping Address"))
    shipping_city = models.CharField(max_length=100, blank=True, verbose_name=_("Shipping City"))
    shipping_postal_code = models.CharField(max_length=20, blank=True, verbose_name=_("Shipping Postal Code"))
    shipping_country = models.CharField(max_length=100, blank=True, verbose_name=_("Shipping Country"))
    shipping_phone = models.CharField(max_length=20, blank=True, verbose_name=_("Shipping Phone"))
    
    # Order totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Subtotal"))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Shipping Cost"))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Tax Amount"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Total Amount"))
    
    # Status and tracking
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending', verbose_name=_("Order Status"))
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name=_("Payment Status"))
    
    # Notes
    order_notes = models.TextField(blank=True, verbose_name=_("Order Notes"))
    admin_notes = models.TextField(blank=True, verbose_name=_("Admin Notes"))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Generate unique order number"""
        import random
        import string
        from django.utils import timezone
        
        date_str = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"ORD{date_str}{random_str}"

    @property
    def full_billing_name(self):
        return f"{self.billing_first_name} {self.billing_last_name}"

    @property
    def full_shipping_name(self):
        if self.different_shipping:
            return f"{self.shipping_first_name} {self.shipping_last_name}"
        return self.full_billing_name

    @property
    def shipping_address_display(self):
        if self.different_shipping:
            return f"{self.shipping_address}, {self.shipping_city}, {self.shipping_postal_code}"
        return f"{self.billing_address}, {self.billing_city}, {self.billing_postal_code}"


class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_("Order"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("Product"))
    product_name = models.CharField(max_length=200, verbose_name=_("Product Name"))  # Store name at time of order
    product_model = models.CharField(max_length=50, verbose_name=_("Product Model"))  # Store model at time of order
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price"))  # Store price at time of order
    quantity = models.PositiveIntegerField(verbose_name=_("Quantity"))

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def total_price(self):
        return self.price * self.quantity


class Payment(models.Model):
    """Payment transactions"""
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', _('Credit Card')),
        ('debit_card', _('Debit Card')),
        ('bank_transfer', _('Bank Transfer')),
        ('cash_on_delivery', _('Cash on Delivery')),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment', verbose_name=_("Order"))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name=_("Payment Method"))
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Amount"))
    currency = models.CharField(max_length=3, default='GEL', verbose_name=_("Currency"))
    
    # Card information (encrypted in real implementation)
    card_last_four = models.CharField(max_length=4, blank=True, verbose_name=_("Card Last 4 Digits"))
    card_brand = models.CharField(max_length=20, blank=True, verbose_name=_("Card Brand"))
    
    # Transaction details
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name=_("Transaction ID"))
    gateway_response = models.TextField(blank=True, verbose_name=_("Gateway Response"))
    
    # Status
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name=_("Status"))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Processed At"))

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')

    def __str__(self):
        return f"Payment for Order #{self.order.order_number}"