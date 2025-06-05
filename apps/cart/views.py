from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from apps.products.models import Product
from .models import Cart, CartItem, Wishlist, WishlistItem
import json


def get_or_create_cart(request):
    """Get or create cart for authenticated user only"""
    if not request.user.is_authenticated:
        return None
    cart, created = Cart.objects.get_or_create(user=request.user)
    return cart


@login_required
@require_POST
def add_to_cart(request, product_id):
    """Add product to cart - requires login"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    if not product.is_available:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Product is out of stock'})
        messages.error(request, 'This product is out of stock.')
        return redirect('products:product_detail', slug=product.slug)
    
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if item already exists in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Item already exists, update quantity
        cart_item.quantity += quantity
        # Check stock
        if cart_item.quantity > product.stock_quantity:
            cart_item.quantity = product.stock_quantity
            message = f'Only {product.stock_quantity} items available. Cart updated.'
        else:
            message = f'Updated {product.name} quantity in cart.'
        cart_item.save()
    else:
        message = f'Added {product.name} to cart.'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True, 
            'message': message,
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price)
        })
    
    messages.success(request, message)
    return redirect('cart:cart_detail')


@login_required
def cart_detail(request):
    """Display cart contents - requires login"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all() if cart else []
    context = {
        'cart': cart,
        'cart_items': cart_items
    }
    return render(request, 'cart/cart_detail.html', context)


@login_required
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity - requires login"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        message = f'Removed {cart_item.product.name} from cart.'
    else:
        # Check stock
        if quantity > cart_item.product.stock_quantity:
            quantity = cart_item.product.stock_quantity
            message = f'Only {quantity} items available. Quantity updated.'
        else:
            message = f'Updated {cart_item.product.name} quantity.'
        
        cart_item.quantity = quantity
        cart_item.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price),
            'item_total': str(cart_item.total_price) if quantity > 0 else '0'
        })
    
    messages.success(request, message)
    return redirect('cart:cart_detail')


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart - requires login"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = cart_item.product.name
    cart_item.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Removed {product_name} from cart.',
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price)
        })
    
    messages.success(request, f'Removed {product_name} from cart.')
    return redirect('cart:cart_detail')


@login_required
def clear_cart(request):
    """Clear all items from cart - requires login"""
    cart = get_or_create_cart(request)
    if cart:
        cart.clear()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Cart cleared.',
            'cart_total_items': 0,
            'cart_total_price': '0.00'
        })
    
    messages.success(request, 'Cart cleared.')
    return redirect('cart:cart_detail')


# Wishlist Views
@login_required
@require_POST
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    wishlist_item, created = WishlistItem.objects.get_or_create(
        wishlist=wishlist,
        product=product
    )
    
    if created:
        message = f'Added {product.name} to your wishlist.'
        success = True
    else:
        message = f'{product.name} is already in your wishlist.'
        success = False
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success,
            'message': message,
            'in_wishlist': True
        })
    
    if success:
        messages.success(request, message)
    else:
        messages.info(request, message)
    
    return redirect('products:product_detail', slug=product.slug)


@login_required
def wishlist_detail(request):
    """Display user's wishlist"""
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_items = wishlist.items.select_related('product').all()
    except Wishlist.DoesNotExist:
        wishlist_items = []
    
    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, 'cart/wishlist_detail.html', context)


@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    product = get_object_or_404(Product, id=product_id)
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_item = WishlistItem.objects.get(wishlist=wishlist, product=product)
        wishlist_item.delete()
        message = f'Removed {product.name} from your wishlist.'
        success = True
    except (Wishlist.DoesNotExist, WishlistItem.DoesNotExist):
        message = f'{product.name} was not in your wishlist.'
        success = False
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success,
            'message': message,
            'in_wishlist': False
        })
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('cart:wishlist_detail')


@login_required
def move_to_cart_from_wishlist(request, product_id):
    """Move item from wishlist to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    if not product.is_available:
        messages.error(request, 'This product is out of stock.')
        return redirect('cart:wishlist_detail')
    
    # Add to cart
    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    # Remove from wishlist
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_item = WishlistItem.objects.get(wishlist=wishlist, product=product)
        wishlist_item.delete()
    except (Wishlist.DoesNotExist, WishlistItem.DoesNotExist):
        pass
    
    messages.success(request, f'Moved {product.name} to cart.')
    return redirect('cart:wishlist_detail')