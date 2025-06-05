from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Category, Product, ProductImage, ProductSpecification


class ProductImageInline(admin.TabularInline):
    """Inline admin for product images"""
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'alt_text_ka', 'is_main', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "No image"
    image_preview.short_description = "Preview"


class ProductSpecificationInline(admin.TabularInline):
    """Inline admin for product specifications"""
    model = ProductSpecification
    extra = 1
    fields = ['name', 'name_ka', 'value', 'value_ka', 'is_important', 'order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Categories"""
    list_display = ['name', 'name_ka', 'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'name_ka', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'product_count']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'name_ka', 'slug', 'image')
        }),
        (_('Content'), {
            'fields': ('description', 'description_ka')
        }),
        (_('Settings'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def product_count(self, obj):
        """Show number of products in this category"""
        return obj.products.count()
    product_count.short_description = _('Products Count')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Products"""
    list_display = [
        'model_number', 'name', 'category', 'formatted_price', 
        'stock_quantity', 'is_in_stock', 'is_active', 'is_featured'
    ]
    list_filter = [
        'category', 'is_active', 'is_featured', 'is_in_stock', 
        'created_at', 'updated_at'
    ]
    search_fields = ['model_number', 'name', 'name_ka', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'main_image_preview']
    inlines = [ProductImageInline, ProductSpecificationInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('model_number', 'name', 'name_ka', 'slug', 'category')
        }),
        (_('Content'), {
            'fields': ('description', 'description_ka', 'short_description', 'short_description_ka')
        }),
        (_('Pricing'), {
            'fields': ('price',)
        }),
        (_('Technical Specifications'), {
            'fields': (
                'power', 'voltage', 'frequency', 'temperature_settings', 
                'air_flow_settings', 'cable_length', 'weight', 'material',
                'noise_level', 'motor_type', 'heating_element_type'
            ),
            'classes': ('collapse',)
        }),
        (_('Additional Information'), {
            'fields': ('additional_specs', 'includes', 'includes_ka'),
            'classes': ('collapse',)
        }),
        (_('Inventory'), {
            'fields': ('stock_quantity', 'is_in_stock')
        }),
        (_('SEO & Marketing'), {
            'fields': ('meta_title', 'meta_description', 'keywords'),
            'classes': ('collapse',)
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_featured')
        }),
        (_('Images'), {
            'fields': ('main_image_preview',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def main_image_preview(self, obj):
        """Show main product image preview"""
        main_image = obj.get_main_image()
        if main_image:
            return format_html('<img src="{}" width="150" height="150" style="object-fit: cover;" />', main_image.url)
        return "No main image"
    main_image_preview.short_description = _('Main Image Preview')

    def formatted_price(self, obj):
        """Display formatted price"""
        return obj.formatted_price()
    formatted_price.short_description = _('Price')
    formatted_price.admin_order_field = 'price'

    # Custom actions
    actions = ['make_active', 'make_inactive', 'mark_as_featured', 'mark_as_not_featured']

    def make_active(self, request, queryset):
        """Mark selected products as active"""
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} products marked as active.")
    make_active.short_description = _("Mark selected products as active")

    def make_inactive(self, request, queryset):
        """Mark selected products as inactive"""
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} products marked as inactive.")
    make_inactive.short_description = _("Mark selected products as inactive")

    def mark_as_featured(self, request, queryset):
        """Mark selected products as featured"""
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} products marked as featured.")
    mark_as_featured.short_description = _("Mark selected products as featured")

    def mark_as_not_featured(self, request, queryset):
        """Mark selected products as not featured"""
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} products marked as not featured.")
    mark_as_not_featured.short_description = _("Mark selected products as not featured")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Admin configuration for Product Images"""
    list_display = ['product', 'image_preview', 'alt_text', 'is_main', 'order']
    list_filter = ['is_main', 'created_at']
    search_fields = ['product__name', 'alt_text']
    readonly_fields = ['image_preview', 'created_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    """Admin configuration for Product Specifications"""
    list_display = ['product', 'name', 'value', 'is_important', 'order']
    list_filter = ['is_important', 'product__category']
    search_fields = ['product__name', 'name', 'value']