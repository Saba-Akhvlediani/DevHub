from .models import Category


def categories_context(request):
    """Add categories to the global template context"""
    categories = Category.objects.filter(is_active=True).order_by('name')
    return {
        'categories': categories,
    } 