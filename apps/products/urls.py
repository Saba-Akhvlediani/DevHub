from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product listing
    path('', views.ProductListView.as_view(), name='product_list'),
    
    # Category views
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Product detail
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Search and filtering
    path('search/', views.ProductSearchView.as_view(), name='product_search'),
]