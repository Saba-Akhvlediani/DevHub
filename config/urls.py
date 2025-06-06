# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from apps.products.views import home_view

# Use dynamic admin URL from settings
admin_url = getattr(settings, 'ADMIN_URL', 'admin/')

urlpatterns = [
    # Admin
    path(admin_url, admin.site.urls),
    
    # Main site
    path('', home_view, name='home'),
    
    # Core apps
    path('products/', include('apps.products.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('accounts/', include('apps.accounts.urls')),
    
    # New features
    path('api/v1/', include('apps.api.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    
    # Favicon redirect
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Georgian Equipment Admin"
admin.site.site_title = "Georgian Equipment Admin Portal"
admin.site.index_title = "Welcome to Georgian Equipment Administration"