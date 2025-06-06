# apps/common/middleware.py
import logging
from django.core.cache import cache
from django.http import HttpResponseTooManyRequests
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib import messages

logger = logging.getLogger(__name__)

class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware to prevent abuse"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        if request.path.startswith('/admin/'):
            return None
            
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Different limits for different endpoints
        if request.path.startswith('/cart/add/'):
            return self.check_rate_limit(request, ip, 'cart_add', max_requests=10, window=60)
        elif request.path.startswith('/orders/'):
            return self.check_rate_limit(request, ip, 'orders', max_requests=5, window=300)
        elif request.method == 'POST':
            return self.check_rate_limit(request, ip, 'post', max_requests=20, window=60)
        
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_rate_limit(self, request, ip, action, max_requests, window):
        cache_key = f"rate_limit_{action}_{ip}"
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= max_requests:
            logger.warning(f"Rate limit exceeded for {ip} on {action}")
            return HttpResponseTooManyRequests("Too many requests. Please try again later.")
        
        cache.set(cache_key, current_requests + 1, window)
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses"""
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
            "img-src 'self' data: blob:; "
            "font-src 'self' cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """Log important user actions for security auditing"""
    
    def process_response(self, request, response):
        if request.user.is_authenticated and request.method == 'POST':
            # Log important actions
            if 'login' in request.path:
                logger.info(f"User {request.user.username} logged in from {self.get_client_ip(request)}")
            elif 'orders' in request.path:
                logger.info(f"User {request.user.username} placed order from {self.get_client_ip(request)}")
            elif 'cart/add' in request.path:
                logger.info(f"User {request.user.username} added item to cart")
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip