# apps/products/search.py
from django.db import models
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.cache import cache
import json

class ProductSearchManager:
    """Enhanced product search with caching and PostgreSQL full-text search"""
    
    @staticmethod
    def search_products(query, category=None, min_price=None, max_price=None, 
                       in_stock=None, sort_by='relevance', limit=20):
        """
        Advanced product search with multiple filters and sorting options
        """
        from .models import Product
        
        # Create cache key
        cache_key = f"search_{hash(str({
            'query': query,
            'category': category,
            'min_price': min_price,
            'max_price': max_price,
            'in_stock': in_stock,
            'sort_by': sort_by,
            'limit': limit
        }))}"
        
        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Base queryset
        queryset = Product.objects.filter(is_active=True).select_related('category')
        
        # Apply filters
        if category:
            queryset = queryset.filter(category__slug=category)
        
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        
        if in_stock:
            queryset = queryset.filter(is_in_stock=True, stock_quantity__gt=0)
        
        # Full-text search if query provided
        if query:
            search_vector = SearchVector(
                'name', weight='A',
                'name_ka', weight='A',
                'description', weight='B',
                'model_number', weight='A',
                'category__name', weight='C'
            )
            search_query = SearchQuery(query)
            queryset = queryset.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(search=search_query)
        
        # Apply sorting
        if sort_by == 'price_low':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'relevance' and query:
            queryset = queryset.order_by('-rank', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        # Execute query with prefetch
        results = queryset.prefetch_related('images')[:limit]
        
        # Cache results for 15 minutes
        cache.set(cache_key, list(results), 900)
        
        return results
    
    @staticmethod
    def get_search_suggestions(query, limit=5):
        """Get search suggestions based on partial query"""
        from .models import Product
        
        if len(query) < 2:
            return []
        
        cache_key = f"suggestions_{hash(query)}"
        cached_suggestions = cache.get(cache_key)
        if cached_suggestions:
            return cached_suggestions
        
        # Get product names that start with the query
        suggestions = Product.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(model_number__icontains=query),
            is_active=True
        ).values_list('name', 'model_number')[:limit]
        
        # Flatten and deduplicate
        suggestion_list = []
        for name, model in suggestions:
            if query.lower() in name.lower() and name not in suggestion_list:
                suggestion_list.append(name)
            if query.lower() in model.lower() and model not in suggestion_list:
                suggestion_list.append(model)
        
        # Cache for 1 hour
        cache.set(cache_key, suggestion_list[:limit], 3600)
        return suggestion_list[:limit]


# apps/products/views.py - Update your search view
from django.http import JsonResponse
from django.db.models import Q, Min, Max
from .search import ProductSearchManager

class ProductSearchView(ListView):
    """Enhanced search view with AJAX support"""
    model = Product
    template_name = 'products/product_search.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        category = self.request.GET.get('category')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        in_stock = self.request.GET.get('in_stock') == 'on'
        sort_by = self.request.GET.get('sort_by', 'relevance')
        
        # Convert price strings to floats
        try:
            min_price = float(min_price) if min_price else None
        except (ValueError, TypeError):
            min_price = None
            
        try:
            max_price = float(max_price) if max_price else None
        except (ValueError, TypeError):
            max_price = None
        
        if query:
            return ProductSearchManager.search_products(
                query=query,
                category=category,
                min_price=min_price,
                max_price=max_price,
                in_stock=in_stock,
                sort_by=sort_by,
                limit=50  # Higher limit for pagination
            )
        return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['categories'] = Category.objects.filter(is_active=True)
        
        # Get price range for filters
        price_range = Product.objects.filter(is_active=True).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['price_range'] = price_range
        
        return context

def search_suggestions(request):
    """AJAX endpoint for search suggestions"""
    query = request.GET.get('q', '').strip()
    suggestions = ProductSearchManager.get_search_suggestions(query)
    return JsonResponse({'suggestions': suggestions})