from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django_filters.views import FilterView
from .models import Product, Category
from .filters import ProductFilter


class ProductListView(FilterView):
    """Display all active products with filtering"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    filterset_class = ProductFilter
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['featured_products'] = Product.objects.filter(is_active=True, is_featured=True)[:6]
        return context


class ProductDetailView(DetailView):
    """Display individual product details"""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'specifications')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Related products from same category
        context['related_products'] = Product.objects.filter(
            category=self.object.category,
            is_active=True
        ).exclude(id=self.object.id)[:4]
        
        return context


class CategoryDetailView(DetailView):
    """Display products in a specific category"""
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        return Category.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.object.products.filter(is_active=True).prefetch_related('images')
        return context


class ProductSearchView(ListView):
    """Search products"""
    model = Product
    template_name = 'products/product_search.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Product.objects.filter(
                Q(name__icontains=query) |
                Q(name_ka__icontains=query) |
                Q(description__icontains=query) |
                Q(description_ka__icontains=query) |
                Q(model_number__icontains=query),
                is_active=True
            ).select_related('category').prefetch_related('images')
        return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


def home_view(request):
    """Homepage view"""
    context = {
        'featured_products': Product.objects.filter(is_active=True, is_featured=True)[:8],
        'categories': Category.objects.filter(is_active=True)[:6],
        'latest_products': Product.objects.filter(is_active=True).order_by('-created_at')[:8],
    }
    return render(request, 'home.html', context)