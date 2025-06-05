from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.cart.models import Cart, CartItem
from apps.cart.views import get_or_create_cart
from .models import Order, OrderItem, Payment
from .forms import CheckoutForm, PaymentForm
import json
import random
import string


@login_required
def checkout_view(request):
    """Checkout page - requires login"""
    cart = get_or_create_cart(request)
    
    if not cart:
        messages.error(request, 'Please login to access checkout.')
        return redirect('accounts:login')
    
    cart_items = cart.items.select_related('product').all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')
    
    # Calculate totals
    subtotal = cart.total_price
    shipping_cost = 0  # Free shipping for now
    tax_amount = 0  # No tax for now
    total_amount = subtotal + shipping_cost + tax_amount
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order
            order = Order.objects.create(
                user=request.user,  # Always authenticated now
                email=form.cleaned_data['email'],
                billing_first_name=form.cleaned_data['billing_first_name'],
                billing_last_name=form.cleaned_data['billing_last_name'],
                billing_company=form.cleaned_data['billing_company'],
                billing_address=form.cleaned_data['billing_address'],
                billing_city=form.cleaned_data['billing_city'],
                billing_postal_code=form.cleaned_data['billing_postal_code'],
                billing_country=form.cleaned_data['billing_country'],
                billing_phone=form.cleaned_data['billing_phone'],
                different_shipping=form.cleaned_data['different_shipping'],
                shipping_first_name=form.cleaned_data.get('shipping_first_name', ''),
                shipping_last_name=form.cleaned_data.get('shipping_last_name', ''),
                shipping_company=form.cleaned_data.get('shipping_company', ''),
                shipping_address=form.cleaned_data.get('shipping_address', ''),
                shipping_city=form.cleaned_data.get('shipping_city', ''),
                shipping_postal_code=form.cleaned_data.get('shipping_postal_code', ''),
                shipping_country=form.cleaned_data.get('shipping_country', ''),
                shipping_phone=form.cleaned_data.get('shipping_phone', ''),
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax_amount=tax_amount,
                total_amount=total_amount,
                order_notes=form.cleaned_data['order_notes'],
            )
            
            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    product_model=cart_item.product.model_number,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity,
                )
            
            # Store order ID in session for payment
            request.session['order_id'] = order.id
            
            return redirect('orders:payment', order_id=order.id)
    else:
        # Pre-fill form for authenticated users
        initial_data = {
            'email': request.user.email,
            'billing_first_name': request.user.first_name,
            'billing_last_name': request.user.last_name,
        }
        form = CheckoutForm(initial=initial_data)
    
    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def payment_view(request, order_id):
    """Payment page - requires login"""
    order = get_object_or_404(Order, id=order_id, user=request.user)  # Ensure order belongs to user
    
    # Check if this order belongs to the current session
    session_order_id = request.session.get('order_id')
    if session_order_id != order.id:
        messages.error(request, 'Invalid order access.')
        return redirect('cart:cart_detail')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Process payment
            payment_result = process_payment(order, form.cleaned_data)
            
            if payment_result['success']:
                # Clear cart
                cart = get_or_create_cart(request)
                if cart:
                    cart.clear()
                
                # Clear order from session
                if 'order_id' in request.session:
                    del request.session['order_id']
                
                messages.success(request, f'Payment successful! Your order #{order.order_number} has been placed.')
                return redirect('orders:order_success', order_id=order.id)
            else:
                # Payment failed - store error message in session and redirect
                request.session['payment_error'] = payment_result.get('message', 'Payment processing failed. Please try again.')
                return redirect('orders:payment_failed', order_id=order.id)
    else:
        form = PaymentForm()
    
    context = {
        'order': order,
        'form': form,
    }
    return render(request, 'orders/payment.html', context)


def process_payment(order, payment_data):
    """Process payment (simplified simulation)"""
    try:
        print(f"Processing payment for order {order.order_number}")  # Debug
        print(f"Card number from form: {payment_data['card_number']}")  # Debug
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_data['payment_method'],
            amount=order.total_amount,
            currency='GEL',
            card_last_four=payment_data['card_number'][-4:],
            card_brand=get_card_brand(payment_data['card_number']),
            transaction_id=generate_transaction_id(),
            status='processing'
        )
        
        # Simulate payment processing
        # In real implementation, integrate with payment gateway
        payment_result = simulate_payment_gateway(payment_data)
        
        print(f"Payment result: {payment_result}")  # Debug
        
        if payment_result['success']:
            payment.status = 'completed'
            payment.processed_at = timezone.now()
            payment.gateway_response = json.dumps(payment_result)
            
            order.payment_status = 'completed'
            order.order_status = 'processing'
            
            # Update product stock
            for item in order.items.all():
                product = item.product
                if product.stock_quantity >= item.quantity:
                    product.stock_quantity -= item.quantity
                    if product.stock_quantity == 0:
                        product.is_in_stock = False
                    product.save()
            
            payment.save()
            order.save()
            return {'success': True, 'message': 'Payment completed successfully'}
        else:
            payment.status = 'failed'
            payment.gateway_response = json.dumps(payment_result)
            payment.save()
            
            order.payment_status = 'failed'
            order.save()
            return {
                'success': False, 
                'message': payment_result.get('message', 'Payment processing failed')
            }
            
    except Exception as e:
        print(f"Payment processing error: {e}")  # Debug
        return {'success': False, 'message': 'An error occurred while processing payment'}


def payment_failed_view(request, order_id):
    """Payment failed page"""
    order = get_object_or_404(Order, id=order_id)
    
    # Get error message from session and clear it
    error_message = request.session.pop('payment_error', '')
    
    context = {
        'order': order,
        'error_message': error_message,
    }
    return render(request, 'orders/payment_failed.html', context)


def simulate_payment_gateway(payment_data):
    """Simulate payment gateway response"""
    # Remove spaces and get clean card number
    card_number = payment_data['card_number'].replace(' ', '').replace('-', '')
    
    print(f"Processing card number: {card_number}")  # Debug line
    
    # Test cards for different scenarios
    if card_number == '4111111111111111':  # Successful test card
        return {
            'success': True,
            'transaction_id': generate_transaction_id(),
            'message': 'Payment processed successfully',
            'gateway': 'test_gateway'
        }
    elif card_number.startswith('4000000000000002'):  # Declined test card
        return {
            'success': False,
            'error_code': 'DECLINED',
            'message': 'Card declined by issuing bank',
            'gateway': 'test_gateway'
        }
    elif card_number.startswith('4000'):  # Other declined test cards
        return {
            'success': False,
            'error_code': 'DECLINED',
            'message': 'Card declined',
            'gateway': 'test_gateway'
        }
    else:
        # For other cards, randomly succeed or fail (90% success rate)
        import random
        if random.random() < 0.9:
            return {
                'success': True,
                'transaction_id': generate_transaction_id(),
                'message': 'Payment processed successfully',
                'gateway': 'test_gateway'
            }
        else:
            return {
                'success': False,
                'error_code': 'PROCESSING_ERROR',
                'message': 'Payment processing failed',
                'gateway': 'test_gateway'
            }


def get_card_brand(card_number):
    """Determine card brand from card number"""
    card_number = card_number.replace(' ', '')
    
    if card_number.startswith('4'):
        return 'Visa'
    elif card_number.startswith(('51', '52', '53', '54', '55')):
        return 'Mastercard'
    elif card_number.startswith(('34', '37')):
        return 'American Express'
    else:
        return 'Unknown'


def generate_transaction_id():
    """Generate unique transaction ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


def order_success_view(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
    }
    return render(request, 'orders/order_success.html', context)


def order_detail_view(request, order_id):
    """Order detail page"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check access permissions
    if request.user.is_authenticated:
        if order.user != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('home')
    else:
        messages.error(request, 'Please log in to view your orders.')
        return redirect('home')
    
    context = {
        'order': order,
    }
    return render(request, 'orders/order_detail.html', context)