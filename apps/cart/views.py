from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from apps.products.models import Product
from .models import Cart, CartItem, Wishlist, WishlistItem, CompareList, CompareItem
import json


def get_or_create_cart(request):
    """Get or create cart for both authenticated and anonymous users"""
    if request.user.is_authenticated:
        # For authenticated users, use user-based cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Check if there's a session cart to merge
        session_key = request.session.session_key
        if session_key:
            try:
                session_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
                if session_cart.items.exists():
                    # Merge session cart with user cart
                    session_cart.merge_with_user_cart(cart)
                    session_cart.delete()
            except Cart.DoesNotExist:
                pass
        
        return cart
    else:
        # For anonymous users, use session-based cart
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(
            session_key=session_key,
            user__isnull=True
        )
        return cart


def get_or_create_wishlist(request):
    """Get or create wishlist for both authenticated and anonymous users"""
    if request.user.is_authenticated:
        # For authenticated users, use user-based wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        # Check if there's a session wishlist to merge
        session_key = request.session.session_key
        if session_key:
            try:
                session_wishlist = Wishlist.objects.get(session_key=session_key, user__isnull=True)
                if session_wishlist.items.exists():
                    # Merge session wishlist with user wishlist
                    session_wishlist.merge_with_user_wishlist(wishlist)
                    session_wishlist.delete()
            except Wishlist.DoesNotExist:
                pass
        
        return wishlist
    else:
        # For anonymous users, use session-based wishlist
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        wishlist, created = Wishlist.objects.get_or_create(
            session_key=session_key,
            user__isnull=True
        )
        return wishlist


def get_or_create_compare_list(request):
    """Get or create compare list for both authenticated and anonymous users"""
    if request.user.is_authenticated:
        compare_list, created = CompareList.objects.get_or_create(user=request.user)
        
        # Check if there's a session compare list to merge
        session_key = request.session.session_key
        if session_key:
            try:
                session_compare = CompareList.objects.get(session_key=session_key)
                if created:
                    # Move all items from session compare list to user's compare list
                    session_compare.items.all().update(compare_list=compare_list)
                session_compare.delete()
            except CompareList.DoesNotExist:
                pass
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        compare_list, created = CompareList.objects.get_or_create(session_key=session_key)
    
    return compare_list


# NO @login_required - WORKS FOR EVERYONE
@require_POST
def add_to_cart(request, product_id):
    """Add product to cart - works for both authenticated and anonymous users"""
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


# NO @login_required - WORKS FOR EVERYONE
def cart_detail(request):
    """Display cart contents - works for both authenticated and anonymous users"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all() if cart else []
    
    context = {
        'cart': cart,
        'cart_items': cart_items
    }
    return render(request, 'cart/cart_detail.html', context)


# NO @login_required - WORKS FOR EVERYONE
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity - works for both authenticated and anonymous users"""
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


# NO @login_required - WORKS FOR EVERYONE
@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart - works for both authenticated and anonymous users"""
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


# NO @login_required - WORKS FOR EVERYONE
def clear_cart(request):
    """Clear all items from cart - works for both authenticated and anonymous users"""
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


# WISHLIST VIEWS - NO @login_required - WORKS FOR EVERYONE
@require_POST
def add_to_wishlist(request, product_id):
    """Add product to wishlist - works for both authenticated and anonymous users"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        wishlist = get_or_create_wishlist(request)
        
        # Check if item already exists
        if wishlist.items.filter(product=product).exists():
            success = False
            message = f'{product.name} is already in your wishlist.'
        else:
            WishlistItem.objects.create(wishlist=wishlist, product=product)
            success = True
            message = f'Added {product.name} to your wishlist.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message,
                'wishlist_total_items': wishlist.total_items
            })
        
        if success:
            messages.success(request, message)
        else:
            messages.info(request, message)
        
        return redirect('products:product_detail', slug=product.slug)
    except Exception as e:
        print(f"Error adding to wishlist: {str(e)}")  # Debug log
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while adding to wishlist. Please try again.'
            }, status=500)
        messages.error(request, 'An error occurred while adding to wishlist. Please try again.')
        return redirect('products:product_detail', slug=product.slug)


# NO @login_required - WORKS FOR EVERYONE
def wishlist_detail(request):
    """Display user's wishlist - works for both authenticated and anonymous users"""
    try:
        wishlist = get_or_create_wishlist(request)
        wishlist_items = wishlist.items.select_related('product').all()
        
        context = {
            'wishlist': wishlist,
            'wishlist_items': wishlist_items,
            'cart_total_items': get_or_create_cart(request).total_items
        }
        return render(request, 'cart/wishlist_detail.html', context)
    except Exception as e:
        print(f"Error displaying wishlist: {str(e)}")  # Debug log
        messages.error(request, 'An error occurred while loading your wishlist. Please try again.')
        return redirect('home')


# NO @login_required - WORKS FOR EVERYONE
@require_POST
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist - works for both authenticated and anonymous users"""
    try:
        product = get_object_or_404(Product, id=product_id)
        wishlist = get_or_create_wishlist(request)
        
        try:
            wishlist_item = wishlist.items.get(product=product)
            wishlist_item.delete()
            message = f'Removed {product.name} from wishlist.'
            success = True
        except WishlistItem.DoesNotExist:
            message = f'{product.name} was not in your wishlist.'
            success = False
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message,
                'wishlist_total_items': wishlist.total_items
            })
        
        if success:
            messages.success(request, message)
        else:
            messages.info(request, message)
        
        return redirect('cart:wishlist_detail')
    except Exception as e:
        print(f"Error removing from wishlist: {str(e)}")  # Debug log
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while removing from wishlist. Please try again.'
            }, status=500)
        messages.error(request, 'An error occurred while removing from wishlist. Please try again.')
        return redirect('cart:wishlist_detail')


# NO @login_required - WORKS FOR EVERYONE
@require_POST
def move_to_cart_from_wishlist(request, product_id):
    """Move item from wishlist to cart - works for both authenticated and anonymous users"""
    try:
        product = get_object_or_404(Product, id=product_id)
        wishlist = get_or_create_wishlist(request)
        cart = get_or_create_cart(request)
        
        try:
            # Remove from wishlist
            wishlist_item = wishlist.items.get(product=product)
            wishlist_item.delete()
            
            # Add to cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': 1}
            )
            
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            
            message = f'Moved {product.name} to cart.'
            success = True
        except WishlistItem.DoesNotExist:
            message = f'{product.name} was not in your wishlist.'
            success = False
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message,
                'wishlist_total_items': wishlist.total_items,
                'cart_total_items': cart.total_items
            })
        
        if success:
            messages.success(request, message)
        else:
            messages.info(request, message)
        
        return redirect('cart:wishlist_detail')
    except Exception as e:
        print(f"Error moving item to cart: {str(e)}")  # Debug log
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while moving item to cart. Please try again.'
            }, status=500)
        messages.error(request, 'An error occurred while moving item to cart. Please try again.')
        return redirect('cart:wishlist_detail')


def get_cart_count(request):
    """Helper function to get cart count for templates"""
    cart = get_or_create_cart(request)
    return cart.total_items if cart else 0


def get_wishlist_count(request):
    """Helper function to get wishlist count for templates"""
    wishlist = get_or_create_wishlist(request)
    return wishlist.items.count() if wishlist else 0


@require_POST
def add_to_compare(request, product_id):
    """Add a product to comparison list"""
    compare_list = get_or_create_compare_list(request)
    product = get_object_or_404(Product, id=product_id)
    
    # Check if product is already in compare list
    if CompareItem.objects.filter(compare_list=compare_list, product=product).exists():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Product is already in your comparison list.',
                'compare_total_items': compare_list.items.count()
            })
        messages.info(request, 'Product is already in your comparison list.')
        return redirect('cart:compare_detail') if request.POST.get('redirect_to_compare') else redirect('products:product_detail', slug=product.slug)
    
    # Check if compare list has reached maximum items (e.g., 4)
    if compare_list.items.count() >= 4:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'You can compare up to 4 products at a time. Please remove a product first.',
                'compare_total_items': compare_list.items.count()
            })
        messages.warning(request, 'You can compare up to 4 products at a time. Please remove a product first.')
        return redirect('cart:compare_detail') if request.POST.get('redirect_to_compare') else redirect('products:product_detail', slug=product.slug)
    
    # Add product to compare list
    CompareItem.objects.create(compare_list=compare_list, product=product)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} has been added to your comparison list.',
            'compare_total_items': compare_list.items.count()
        })
    
    messages.success(request, f'{product.name} has been added to your comparison list.')
    return redirect('cart:compare_detail') if request.POST.get('redirect_to_compare') else redirect('products:product_detail', slug=product.slug)


def remove_from_compare(request, product_id):
    """Remove a product from comparison list"""
    compare_list = get_or_create_compare_list(request)
    compare_item = get_object_or_404(CompareItem, compare_list=compare_list, product_id=product_id)
    compare_item.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Product removed from comparison.',
            'compare_total_items': compare_list.items.count()
        })
    
    messages.success(request, 'Product removed from comparison.')
    return redirect('cart:compare_detail')


def clear_compare(request):
    """Remove all products from comparison list"""
    compare_list = get_or_create_compare_list(request)
    compare_list.items.all().delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Comparison list cleared.',
            'compare_total_items': 0
        })
    
    messages.success(request, 'Comparison list cleared.')
    return redirect('cart:compare_detail')


def compare_detail(request):
    """Display comparison page"""
    compare_list = get_or_create_compare_list(request)
    compare_items = compare_list.items.select_related('product').all()
    
    # Get all unique specification keys
    spec_keys = set()
    for item in compare_items:
        product = item.product
        # Add built-in specs
        spec_keys.update([
            'Power', 'Voltage', 'Frequency', 'Temperature Settings',
            'Air Flow Settings', 'Cable Length', 'Weight', 'Material',
            'Noise Level', 'Motor Type', 'Heating Element Type'
        ])
        # Add custom specs if any
        if hasattr(product, 'custom_specs'):
            spec_keys.update(product.custom_specs.keys())
    
    context = {
        'compare_items': compare_items,
        'spec_keys': sorted(spec_keys),
    }
    return render(request, 'cart/compare_detail.html', context)