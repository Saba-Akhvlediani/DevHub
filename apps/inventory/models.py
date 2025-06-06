# apps/inventory/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from apps.products.models import Product

class Supplier(models.Model):
    """Supplier information"""
    
    name = models.CharField(max_length=200, verbose_name=_("Supplier Name"))
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Payment terms
    payment_terms = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=3, default='GEL')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
    
    def __str__(self):
        return self.name

class ProductSupplier(models.Model):
    """Link products to suppliers with pricing"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='suppliers')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    
    supplier_sku = models.CharField(max_length=100, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time_days = models.PositiveIntegerField(default=7)
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['product', 'supplier']
        verbose_name = _('Product Supplier')
        verbose_name_plural = _('Product Suppliers')

class StockMovement(models.Model):
    """Track all stock movements"""
    
    MOVEMENT_TYPES = [
        ('in', _('Stock In')),
        ('out', _('Stock Out')),
        ('adjustment', _('Adjustment')),
        ('transfer', _('Transfer')),
        ('sale', _('Sale')),
        ('return', _('Return')),
        ('damaged', _('Damaged')),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Can be negative for outgoing
    
    # Reference information
    reference_type = models.CharField(max_length=50, blank=True)  # 'order', 'purchase', 'adjustment'
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Details
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Balances
    quantity_before = models.PositiveIntegerField()
    quantity_after = models.PositiveIntegerField()
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Stock Movement')
        verbose_name_plural = _('Stock Movements')
    
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()}: {self.quantity}"

class PurchaseOrder(models.Model):
    """Purchase orders to suppliers"""
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('sent', _('Sent to Supplier')),
        ('confirmed', _('Confirmed')),
        ('partial', _('Partially Received')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    order_date = models.DateField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Purchase Order')
        verbose_name_plural = _('Purchase Orders')
    
    def __str__(self):
        return f"PO #{self.po_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self.generate_po_number()
        super().save(*args, **kwargs)
    
    def generate_po_number(self):
        """Generate unique PO number"""
        from django.utils import timezone
        import random
        import string
        
        date_str = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"PO{date_str}{random_str}"

class PurchaseOrderItem(models.Model):
    """Items in purchase order"""
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['purchase_order', 'product']
        verbose_name = _('Purchase Order Item')
        verbose_name_plural = _('Purchase Order Items')
    
    @property
    def total_cost(self):
        return self.quantity_ordered * self.unit_cost
    
    @property
    def quantity_pending(self):
        return self.quantity_ordered - self.quantity_received

class StockAlert(models.Model):
    """Stock level alerts"""
    
    ALERT_TYPES = [
        ('low_stock', _('Low Stock')),
        ('out_of_stock', _('Out of Stock')),
        ('overstock', _('Overstock')),
        ('reorder_point', _('Reorder Point Reached')),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    
    threshold_quantity = models.PositiveIntegerField()
    current_quantity = models.PositiveIntegerField()
    
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Stock Alert')
        verbose_name_plural = _('Stock Alerts')


# apps/inventory/services.py
from django.db import transaction
from django.utils import timezone
from .models import StockMovement, StockAlert, PurchaseOrder, PurchaseOrderItem
from apps.products.models import Product
import logging

logger = logging.getLogger(__name__)

class InventoryService:
    """Service for inventory management operations"""
    
    @staticmethod
    @transaction.atomic
    def record_stock_movement(product, movement_type, quantity, **kwargs):
        """Record a stock movement and update product quantity"""
        
        # Get current stock
        current_stock = product.stock_quantity
        
        # Calculate new stock level
        if movement_type in ['in', 'return']:
            new_stock = current_stock + abs(quantity)
        elif movement_type in ['out', 'sale', 'damaged']:
            new_stock = max(0, current_stock - abs(quantity))
        elif movement_type == 'adjustment':
            new_stock = max(0, current_stock + quantity)  # quantity can be negative
        else:
            new_stock = current_stock
        
        # Create stock movement record
        movement = StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            quantity_before=current_stock,
            quantity_after=new_stock,
            reference_type=kwargs.get('reference_type', ''),
            reference_id=kwargs.get('reference_id'),
            cost_per_unit=kwargs.get('cost_per_unit'),
            supplier=kwargs.get('supplier'),
            notes=kwargs.get('notes', ''),
            created_by=kwargs.get('user')
        )
        
        # Update product stock
        product.stock_quantity = new_stock
        product.is_in_stock = new_stock > 0
        product.save(update_fields=['stock_quantity', 'is_in_stock'])
        
        # Check for stock alerts
        InventoryService.check_stock_alerts(product)
        
        logger.info(f"Stock movement recorded: {product.name} {movement_type} {quantity}")
        return movement
    
    @staticmethod
    def check_stock_alerts(product):
        """Check and create stock alerts if needed"""
        
        current_stock = product.stock_quantity
        
        # Define thresholds (these could be product-specific settings)
        low_stock_threshold = 10
        reorder_point = 5
        
        # Check for out of stock
        if current_stock == 0:
            StockAlert.objects.get_or_create(
                product=product,
                alert_type='out_of_stock',
                is_resolved=False,
                defaults={
                    'threshold_quantity': 0,
                    'current_quantity': current_stock
                }
            )
        
        # Check for low stock
        elif current_stock <= low_stock_threshold:
            StockAlert.objects.get_or_create(
                product=product,
                alert_type='low_stock',
                is_resolved=False,
                defaults={
                    'threshold_quantity': low_stock_threshold,
                    'current_quantity': current_stock
                }
            )
        
        # Check for reorder point
        if current_stock <= reorder_point:
            StockAlert.objects.get_or_create(
                product=product,
                alert_type='reorder_point',
                is_resolved=False,
                defaults={
                    'threshold_quantity': reorder_point,
                    'current_quantity': current_stock
                }
            )
    
    @staticmethod
    @transaction.atomic
    def receive_purchase_order(po_id, received_items, user):
        """Process received items from purchase order"""
        
        try:
            po = PurchaseOrder.objects.get(id=po_id)
            
            for item_data in received_items:
                po_item = PurchaseOrderItem.objects.get(
                    id=item_data['item_id'],
                    purchase_order=po
                )
                
                quantity_received = item_data['quantity_received']
                
                if quantity_received > 0:
                    # Update PO item
                    po_item.quantity_received += quantity_received
                    po_item.save()
                    
                    # Record stock movement
                    InventoryService.record_stock_movement(
                        product=po_item.product,
                        movement_type='in',
                        quantity=quantity_received,
                        reference_type='purchase_order',
                        reference_id=po.id,
                        cost_per_unit=po_item.unit_cost,
                        supplier=po.supplier,
                        notes=f"Received from PO #{po.po_number}",
                        user=user
                    )
            
            # Update PO status
            all_items_complete = all(
                item.quantity_received >= item.quantity_ordered 
                for item in po.items.all()
            )
            
            if all_items_complete:
                po.status = 'completed'
                po.actual_delivery_date = timezone.now().date()
            else:
                po.status = 'partial'
            
            po.save()
            
            logger.info(f"Purchase order {po.po_number} items received")
            return True
            
        except Exception as e:
            logger.error(f"Error receiving PO items: {str(e)}")
            return False
    
    @staticmethod
    def generate_reorder_suggestions():
        """Generate automatic reorder suggestions based on sales velocity"""
        
        from django.db.models import Avg, Sum
        from datetime import timedelta
        
        suggestions = []
        
        # Get products with low stock or recent sales activity
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=10,
            is_active=True
        ).select_related('category')
        
        for product in low_stock_products:
            # Calculate average daily sales over last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            sales_data = StockMovement.objects.filter(
                product=product,
                movement_type='sale',
                created_at__gte=thirty_days_ago
            ).aggregate(
                total_sold=Sum('quantity'),
                avg_daily_sales=Avg('quantity')
            )
            
            total_sold = abs(sales_data['total_sold'] or 0)
            avg_daily_sales = abs(sales_data['avg_daily_sales'] or 0)
            
            if avg_daily_sales > 0:
                # Calculate suggested reorder quantity
                # Lead time + safety stock
                primary_supplier = product.suppliers.filter(is_primary=True).first()
                lead_time = primary_supplier.lead_time_days if primary_supplier else 14
                
                safety_stock_days = 7  # 1 week safety stock
                suggested_quantity = int(avg_daily_sales * (lead_time + safety_stock_days))
                
                # Respect minimum order quantity
                if primary_supplier and suggested_quantity < primary_supplier.minimum_order_quantity:
                    suggested_quantity = primary_supplier.minimum_order_quantity
                
                suggestions.append({
                    'product': product,
                    'current_stock': product.stock_quantity,
                    'avg_daily_sales': avg_daily_sales,
                    'suggested_quantity': suggested_quantity,
                    'supplier': primary_supplier,
                    'estimated_cost': (primary_supplier.cost_price * suggested_quantity) if primary_supplier else 0
                })
        
        return suggestions


# apps/inventory/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Supplier, ProductSupplier, StockMovement, PurchaseOrder, PurchaseOrderItem, StockAlert

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'currency']
    search_fields = ['name', 'contact_person', 'email']

@admin.register(ProductSupplier)
class ProductSupplierAdmin(admin.ModelAdmin):
    list_display = ['product', 'supplier', 'cost_price', 'lead_time_days', 'is_primary', 'is_active']
    list_filter = ['is_primary', 'is_active', 'supplier']
    search_fields = ['product__name', 'supplier__name', 'supplier_sku']

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'quantity_before', 'quantity_after', 'created_at', 'created_by']
    list_filter = ['movement_type', 'created_at', 'supplier']
    search_fields = ['product__name', 'notes']
    readonly_fields = ['quantity_before', 'quantity_after', 'created_at']

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    readonly_fields = ['total_cost', 'quantity_pending']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'supplier', 'status', 'order_date', 'total_amount', 'created_by']
    list_filter = ['status', 'order_date', 'supplier']
    search_fields = ['po_number', 'supplier__name']
    readonly_fields = ['po_number', 'created_at', 'updated_at']
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('po_number', 'supplier', 'status')
        }),
        ('Dates', {
            'fields': ('order_date', 'expected_delivery_date', 'actual_delivery_date')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'alert_type', 'current_quantity', 'threshold_quantity', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'is_resolved', 'created_at']
    search_fields = ['product__name']
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(
            is_resolved=True,
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(request, f"{queryset.count()} alerts marked as resolved.")
    mark_as_resolved.short_description = "Mark selected alerts as resolved"


# apps/inventory/management/commands/generate_reorder_report.py
from django.core.management.base import BaseCommand
from apps.inventory.services import InventoryService
import csv
from datetime import datetime

class Command(BaseCommand):
    help = 'Generate reorder suggestions report'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output CSV file path',
            default=f'reorder_report_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    def handle(self, *args, **options):
        suggestions = InventoryService.generate_reorder_suggestions()
        
        output_file = options['output']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Product Name', 'Model Number', 'Current Stock', 
                'Daily Sales Average', 'Suggested Quantity', 
                'Supplier', 'Estimated Cost'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for suggestion in suggestions:
                writer.writerow({
                    'Product Name': suggestion['product'].name,
                    'Model Number': suggestion['product'].model_number,
                    'Current Stock': suggestion['current_stock'],
                    'Daily Sales Average': f"{suggestion['avg_daily_sales']:.2f}",
                    'Suggested Quantity': suggestion['suggested_quantity'],
                    'Supplier': suggestion['supplier'].name if suggestion['supplier'] else 'No Primary Supplier',
                    'Estimated Cost': f"{suggestion['estimated_cost']:.2f} ₾"
                })
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated reorder report: {output_file}\n'
                f'Found {len(suggestions)} reorder suggestions'
            )
        )