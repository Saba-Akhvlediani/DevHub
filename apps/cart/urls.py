from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # Cart URLs
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    
    # Wishlist URLs
    path('wishlist/', views.wishlist_detail, name='wishlist_detail'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/<int:product_id>/', views.move_to_cart_from_wishlist, name='move_to_cart_from_wishlist'),
    
    # Compare URLs
    path('compare/', views.compare_detail, name='compare_detail'),
    path('compare/add/<int:product_id>/', views.add_to_compare, name='add_to_compare'),
    path('compare/remove/<int:product_id>/', views.remove_from_compare, name='remove_from_compare'),
    path('compare/clear/', views.clear_compare, name='clear_compare'),
]