import django_filters
from django import forms
from django.db.models import Q
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    """Filter products by various criteria"""
    
    # Search by name
    search = django_filters.CharFilter(
        method='filter_by_name',
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by product name or model...',
            'class': 'form-control'
        }),
        label='Search'
    )
    
    # Category filter
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True),
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Category'
    )
    
    # Price range filters
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        widget=forms.NumberInput(attrs={
            'placeholder': 'From',
            'class': 'form-control',
            'min': '0',
            'step': '1'
        }),
        label='Min Price (₾)'
    )
    
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        widget=forms.NumberInput(attrs={
            'placeholder': 'To',
            'class': 'form-control',
            'min': '0',
            'step': '1'
        }),
        label='Max Price (₾)'
    )
    
    # Sorting options
    SORT_CHOICES = [
        ('', 'Default'),
        ('price', 'Price: Low to High'),
        ('-price', 'Price: High to Low'),
        ('name', 'Name A-Z'),
        ('-name', 'Name Z-A'),
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
    ]
    
    sort_by = django_filters.ChoiceFilter(
        choices=SORT_CHOICES,
        method='filter_by_sort',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Sort By',
        empty_label=None
    )

    def filter_by_name(self, queryset, name, value):
        """Filter products by name or model number"""
        return queryset.filter(
            Q(name__icontains=value) | 
            Q(model_number__icontains=value)
        )

    def filter_by_sort(self, queryset, name, value):
        """Apply sorting to queryset"""
        if value:
            return queryset.order_by(value)
        return queryset

    @property
    def qs(self):
        """Override to ensure active products only"""
        parent = super().qs
        return parent.distinct()

    class Meta:
        model = Product
        fields = ['search', 'category', 'price_min', 'price_max']