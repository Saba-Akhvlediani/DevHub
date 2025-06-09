from .views import get_or_create_cart, get_or_create_wishlist, get_or_create_compare_list


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


def compare_context(request):
    """Add comparison data to the global template context"""
    compare_list = get_or_create_compare_list(request)
    return {
        'compare_total_items': compare_list.total_items if compare_list else 0,
        'compare_list': compare_list,  # Add the compare list object itself
    }