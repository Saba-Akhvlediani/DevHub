from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from django_filters.views import FilterView
from .models import Product, Category
from .filters import ProductFilter
from apps.cart.views import get_cart_count, get_wishlist_count, get_or_create_compare_list


class ProductListView(FilterView):
    """Display all active products with filtering"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    filterset_class = ProductFilter
    paginate_by = 12

    def get_queryset(self):
        """Get base queryset - simplified for debugging"""
        queryset = Product.objects.all().select_related('category').prefetch_related('images')
        print(f"Debug - Total products in database: {queryset.count()}")
        
        # Filter for active products
        active_queryset = queryset.filter(is_active=True)
        print(f"Debug - Active products: {active_queryset.count()}")
        
        return active_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Debug: Print filter results
        if hasattr(self, 'filterset'):
            print(f"Debug - Filtered products count: {self.filterset.qs.count()}")
        
        # Add categories
        categories = Category.objects.filter(is_active=True).order_by('name')
        print(f"Debug - Categories count: {categories.count()}")
        
        context['categories'] = categories
        context['cart_total_items'] = get_cart_count(self.request)
        context['wishlist_total_items'] = get_wishlist_count(self.request)
        context['compare_total_items'] = get_or_create_compare_list(self.request).items.count()
        return context


class ProductDetailView(DetailView):
    """Display individual product details"""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True)\
            .select_related('category')\
            .prefetch_related('images', 'specifications')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_total_items'] = get_cart_count(self.request)
        context['wishlist_total_items'] = get_wishlist_count(self.request)
        context['compare_total_items'] = get_or_create_compare_list(self.request).items.count()
        
        # Get related products
        product = self.get_object()
        related_products = Product.objects.filter(
            Q(category=product.category) & 
            Q(is_active=True) & 
            ~Q(id=product.id)
        ).order_by('-created_at')[:4]
        context['related_products'] = related_products
        
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