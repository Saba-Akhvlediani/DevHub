import django_filters
from django import forms
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    """Filter products by various criteria"""
    
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by product name...',
            'class': 'form-control'
        })
    )
    
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min Price (₾)',
            'class': 'form-control'
        })
    )
    
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max Price (₾)',
            'class': 'form-control'
        })
    )
    
    power = django_filters.CharFilter(
        field_name='power',
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'placeholder': 'Power (e.g., 2000W)',
            'class': 'form-control'
        })
    )
    
    voltage = django_filters.CharFilter(
        field_name='voltage',
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'placeholder': 'Voltage (e.g., 220V)',
            'class': 'form-control'
        })
    )
    
    is_featured = django_filters.BooleanFilter(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    in_stock = django_filters.BooleanFilter(
        field_name='is_in_stock',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Product
        fields = ['name', 'category', 'price_min', 'price_max', 'power', 'voltage', 'is_featured', 'in_stock']