from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from apps.orders.models import Order
from .forms import UserRegistrationForm, UserProfileForm


def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password=form.cleaned_data['password']
            )
            
            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Your account has been created.')
            
            # Redirect to next page or profile
            next_url = request.GET.get('next', 'accounts:profile')
            return redirect(next_url)
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
        'next': request.GET.get('next', '')
    }
    return render(request, 'accounts/register.html', context)


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            
            # Redirect to next page or home
            next_url = request.POST.get('next') or request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    context = {
        'next': request.GET.get('next', '')
    }
    return render(request, 'accounts/login.html', context)


def logout_view(request):
    """User logout"""
    if request.user.is_authenticated:
        messages.success(request, f'Goodbye, {request.user.first_name or request.user.username}!')
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    """User profile page"""
    # Get user's recent orders
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'user': request.user,
        'recent_orders': recent_orders,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def change_password_view(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/change_password.html', context)


@login_required
def order_history_view(request):
    """User's order history"""
    orders_list = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders_list, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/order_history.html', context)


@login_required
def order_detail_view(request, order_id):
    """View specific order details"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('accounts:order_history')
    
    context = {
        'order': order,
    }
    return render(request, 'accounts/order_detail.html', context)