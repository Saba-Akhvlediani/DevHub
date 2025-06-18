from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from django_filters.views import FilterView
from .models import Product, Category
from .filters import ProductFilter
from apps.cart.views import get_cart_count, get_wishlist_count, get_or_create_compare_list, get_or_create_wishlist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


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
        context['wishlist'] = get_or_create_wishlist(self.request)
        
        # Add compare items for button state
        compare_list = get_or_create_compare_list(self.request)
        context['compare_items'] = compare_list.items.all()
        context['compare_product_ids'] = list(compare_list.items.values_list('product_id', flat=True))
        
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
    """Display products in a specific category with pagination, filtering, sorting, and search"""
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    paginate_by = 12

    def get_queryset(self):
        return Category.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = self.object.products.filter(is_active=True).prefetch_related('images')
        request = self.request
        get = request.GET

        # Filtering
        price_min = get.get('price_min')
        price_max = get.get('price_max')
        in_stock = get.get('in_stock')
        search = get.get('search')
        sort_by = get.get('sort_by')

        if price_min:
            products = products.filter(price__gte=price_min)
        if price_max:
            products = products.filter(price__lte=price_max)
        if in_stock:
            products = products.filter(is_in_stock=True)
        if search:
            products = products.filter(
                Q(name__icontains=search) | Q(model_number__icontains=search)
            )
        if sort_by:
            products = products.order_by(sort_by)
        else:
            products = products.order_by('-created_at')

        # Pagination
        paginator = Paginator(products, self.paginate_by)
        page = request.GET.get('page')
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['paginator'] = paginator
        context['products'] = page_obj.object_list
        context['wishlist'] = get_or_create_wishlist(request)
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
        'wishlist': get_or_create_wishlist(request),
    }
    return render(request, 'home.html', context)