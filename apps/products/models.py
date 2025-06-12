from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from PIL import Image
import os


class Category(models.Model):
    """Product categories for organizing industrial equipment"""
    name = models.CharField(max_length=200, unique=True, verbose_name=_("Category Name"))
    name_ka = models.CharField(max_length=200, blank=True, verbose_name=_("Category Name (Georgian)"))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_("URL Slug"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    description_ka = models.TextField(blank=True, verbose_name=_("Description (Georgian)"))
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name=_("Category Image"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ['name']
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:category_detail', args=[self.slug])

    @property
    def product_count(self):
        """Return the number of active products in this category"""
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    """Industrial equipment products"""
    # Basic Information
    model_number = models.CharField(max_length=50, unique=True, verbose_name=_("Model Number"))
    name = models.CharField(max_length=200, verbose_name=_("Product Name"))
    name_ka = models.CharField(max_length=200, blank=True, verbose_name=_("Product Name (Georgian)"))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_("URL Slug"))
    
    # Categories
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name=_("Category"))
    
    # Descriptions
    description = models.TextField(verbose_name=_("Description"))
    description_ka = models.TextField(blank=True, verbose_name=_("Description (Georgian)"))
    short_description = models.CharField(max_length=500, blank=True, verbose_name=_("Short Description"))
    short_description_ka = models.CharField(max_length=500, blank=True, verbose_name=_("Short Description (Georgian)"))
    
    # Pricing (only retail price as requested)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Retail Price (₾)"))
    
    # Technical Specifications
    power = models.CharField(max_length=100, blank=True, verbose_name=_("Power"))
    voltage = models.CharField(max_length=100, blank=True, verbose_name=_("Voltage"))
    frequency = models.CharField(max_length=100, blank=True, verbose_name=_("Frequency"))
    temperature_settings = models.TextField(blank=True, verbose_name=_("Temperature Settings"))
    air_flow_settings = models.TextField(blank=True, verbose_name=_("Air Flow Settings"))
    cable_length = models.CharField(max_length=100, blank=True, verbose_name=_("Cable Length"))
    weight = models.CharField(max_length=100, blank=True, verbose_name=_("Weight"))
    material = models.CharField(max_length=200, blank=True, verbose_name=_("Material"))
    noise_level = models.CharField(max_length=100, blank=True, verbose_name=_("Noise Level"))
    motor_type = models.CharField(max_length=200, blank=True, verbose_name=_("Motor Type"))
    heating_element_type = models.CharField(max_length=200, blank=True, verbose_name=_("Heating Element Type"))
    
    # Additional specifications (JSON field for flexible specs)
    additional_specs = models.JSONField(default=dict, blank=True, verbose_name=_("Additional Specifications"))
    
    # Accessories and includes
    includes = models.TextField(blank=True, verbose_name=_("What's Included"))
    includes_ka = models.TextField(blank=True, verbose_name=_("What's Included (Georgian)"))
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name=_("Stock Quantity"))
    is_in_stock = models.BooleanField(default=True, verbose_name=_("In Stock"))
    
    # SEO and Marketing
    meta_title = models.CharField(max_length=200, blank=True, verbose_name=_("Meta Title"))
    meta_description = models.CharField(max_length=300, blank=True, verbose_name=_("Meta Description"))
    keywords = models.CharField(max_length=500, blank=True, verbose_name=_("Keywords"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Featured Product"))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        indexes = [
            models.Index(fields=['model_number']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f"{self.model_number} - {self.name}"

    def get_absolute_url(self):
        return reverse('products:product_detail', args=[self.slug])

    @property
    def is_available(self):
        """Check if product is available for purchase"""
        return self.is_active and self.is_in_stock and self.stock_quantity > 0

    def formatted_price(self):
        """Return formatted price with currency"""
        return f"{self.price} ₾"

    def get_main_image(self):
        """Get the main product image"""
        main_image = self.images.filter(is_main=True).first()
        return main_image.image if main_image else None

    def get_all_images(self):
        """Get all product images"""
        return self.images.all().order_by('-is_main', 'order')


class ProductImage(models.Model):
    """Product images with support for multiple images per product"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name=_("Product"))
    image = models.ImageField(upload_to='products/', verbose_name=_("Image"))
    alt_text = models.CharField(max_length=200, blank=True, verbose_name=_("Alt Text"))
    alt_text_ka = models.CharField(max_length=200, blank=True, verbose_name=_("Alt Text (Georgian)"))
    is_main = models.BooleanField(default=False, verbose_name=_("Main Image"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ['-is_main', 'order']
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        # Ensure only one main image per product
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)
        
        super().save(*args, **kwargs)
        
        # Optimize image size
        if self.image:
            self.optimize_image()

    def optimize_image(self):
        """Optimize image size for web"""
        try:
            img = Image.open(self.image.path)
            
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Resize if too large
            max_size = (1200, 1200)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(self.image.path, optimize=True, quality=85)
        except Exception as e:
            pass  # If optimization fails, keep original


class ProductSpecification(models.Model):
    """Additional flexible specifications for products"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications', verbose_name=_("Product"))
    name = models.CharField(max_length=200, verbose_name=_("Specification Name"))
    name_ka = models.CharField(max_length=200, blank=True, verbose_name=_("Specification Name (Georgian)"))
    value = models.CharField(max_length=500, verbose_name=_("Value"))
    value_ka = models.CharField(max_length=500, blank=True, verbose_name=_("Value (Georgian)"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    is_important = models.BooleanField(default=False, verbose_name=_("Important Specification"))

    class Meta:
        ordering = ['-is_important', 'order', 'name']
        verbose_name = _('Product Specification')
        verbose_name_plural = _('Product Specifications')

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"