from .views import get_or_create_cart, get_or_create_wishlist


def cart_context(request):
    """Add cart data to the global template context"""
    cart = get_or_create_cart(request)
    return {
        'cart_total_items': cart.total_items if cart else 0,
    }


def wishlist_context(request):
    """Add wishlist data to the global template context"""
    wishlist = get_or_create_wishlist(request)
    return {
        'wishlist_total_items': wishlist.total_items if wishlist else 0,
        'wishlist': wishlist,  # Add the wishlist object itself
    }