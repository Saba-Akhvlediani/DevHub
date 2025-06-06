# apps/api/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from apps.products.models import Product, Category, ProductImage
from apps.orders.models import Order, OrderItem
from apps.cart.models import Cart, CartItem, Wishlist, WishlistItem

class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'name_ka', 'slug', 'description', 'image']

class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer"""
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_main', 'order']

class ProductListSerializer(serializers.ModelSerializer):
    """Product list serializer (lighter version)"""
    category = CategorySerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'name_ka', 'slug', 'model_number',
            'short_description', 'price', 'category', 'main_image',
            'is_available', 'is_featured'
        ]
    
    def get_main_image(self, obj):
        main_image = obj.get_main_image()
        if main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.url)
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed product serializer"""
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    specifications = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'name_ka', 'slug', 'model_number',
            'description', 'description_ka', 'short_description',
            'price', 'category', 'images', 'specifications',
            'power', 'voltage', 'frequency', 'weight', 'material',
            'stock_quantity', 'is_available', 'is_featured',
            'related_products', 'created_at'
        ]
    
    def get_specifications(self, obj):
        return [
            {
                'name': spec.name,
                'name_ka': spec.name_ka,
                'value': spec.value,
                'value_ka': spec.value_ka,
                'is_important': spec.is_important
            }
            for spec in obj.specifications.all()
        ]
    
    def get_related_products(self, obj):
        related = Product.objects.filter(
            category=obj.category,
            is_active=True
        ).exclude(id=obj.id)[:4]
        
        return ProductListSerializer(
            related, 
            many=True, 
            context=self.context
        ).data

class CartItemSerializer(serializers.ModelSerializer):
    """Cart item serializer"""
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price', 'added_at']
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value, is_active=True)
            if not product.is_available:
                raise serializers.ValidationError("Product is not available")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

class CartSerializer(serializers.ModelSerializer):
    """Cart serializer"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']

class WishlistItemSerializer(serializers.ModelSerializer):
    """Wishlist item serializer"""
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'added_at']

class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer"""
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_model', 'price', 'quantity', 'total_price']

class OrderSerializer(serializers.ModelSerializer):
    """Order serializer"""
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'email', 'billing_first_name', 'billing_last_name',
            'total_amount', 'order_status', 'payment_status', 'items',
            'created_at', 'updated_at'
        ]

class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['username', 'date_joined']


# apps/api/views.py
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate
from django.db.models import Q
from apps.products.models import Product, Category
from apps.cart.models import Cart, CartItem, Wishlist, WishlistItem
from apps.orders.models import Order
from apps.recommendations.services import RecommendationEngine
from .serializers import *

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class CategoryListView(generics.ListAPIView):
    """List all categories"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class ProductListView(generics.ListAPIView):
    """List products with filtering and search"""
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        
        # Filtering
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        in_stock = self.request.query_params.get('in_stock')
        featured = self.request.query_params.get('featured')
        
        if category:
            queryset = queryset.filter(category__slug=category)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(name_ka__icontains=search) |
                Q(description__icontains=search) |
                Q(model_number__icontains=search)
            )
        
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        if in_stock == 'true':
            queryset = queryset.filter(is_in_stock=True, stock_quantity__gt=0)
        
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Sorting
        sort_by = self.request.query_params.get('sort_by', 'name')
        if sort_by == 'price_low':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('name')
        
        return queryset

class ProductDetailView(generics.RetrieveAPIView):
    """Get product details"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        
        # Track user behavior
        product = self.get_object()
        recommendation_engine = RecommendationEngine()
        recommendation_engine.track_user_behavior(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            product=product,
            action_type='view',
            request=request
        )
        
        return response

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_login(request):
    """User login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserProfileSerializer(user).data
        })
    else:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def user_logout(request):
    """User logout endpoint"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out'})
    except:
        return Response({'message': 'Already logged out'})

class CartView(generics.RetrieveAPIView):
    """Get user's cart"""
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_cart(request):
    """Add item to cart"""
    serializer = CartItemSerializer(data=request.data)
    
    if serializer.is_valid():
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if item already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Track behavior
        recommendation_engine = RecommendationEngine()
        recommendation_engine.track_user_behavior(
            user=request.user,
            product=product,
            action_type='cart_add',
            request=request
        )
        
        return Response({
            'message': 'Item added to cart',
            'cart_item': CartItemSerializer(cart_item, context={'request': request}).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def update_cart_item(request, item_id):
    """Update or remove cart item"""
    try:
        cart_item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )
    except CartItem.DoesNotExist:
        return Response({
            'error': 'Cart item not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'DELETE':
        cart_item.delete()
        return Response({'message': 'Item removed from cart'})
    
    elif request.method == 'PUT':
        quantity = request.data.get('quantity')
        if quantity is None or quantity < 1:
            return Response({
                'error': 'Invalid quantity'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return Response({
            'message': 'Cart item updated',
            'cart_item': CartItemSerializer(cart_item, context={'request': request}).data
        })

class WishlistView(generics.ListCreateAPIView):
    """Get user's wishlist or add item to wishlist"""
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        wishlist, created = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist.items.select_related('product').all()
    
    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )
        
        if created:
            # Track behavior
            recommendation_engine = RecommendationEngine()
            recommendation_engine.track_user_behavior(
                user=request.user,
                product=product,
                action_type='wishlist_add',
                request=request
            )
            
            return Response({
                'message': 'Item added to wishlist',
                'wishlist_item': WishlistItemSerializer(wishlist_item, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': 'Item already in wishlist'
            }, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_wishlist(request, product_id):
    """Remove item from wishlist"""
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_item = WishlistItem.objects.get(
            wishlist=wishlist,
            product_id=product_id
        )
        wishlist_item.delete()
        
        return Response({'message': 'Item removed from wishlist'})
    except (Wishlist.DoesNotExist, WishlistItem.DoesNotExist):
        return Response({
            'error': 'Item not found in wishlist'
        }, status=status.HTTP_404_NOT_FOUND)

class OrderListView(generics.ListAPIView):
    """Get user's orders"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_recommendations(request, product_id=None):
    """Get product recommendations"""
    
    try:
        base_product = None
        if product_id:
            base_product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({
            'error': 'Product not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    recommendation_engine = RecommendationEngine()
    recommendations = recommendation_engine.get_recommendations(
        user=request.user if request.user.is_authenticated else None,
        product=base_product,
        session_key=request.session.session_key,
        limit=10
    )
    
    serializer = ProductListSerializer(
        recommendations,
        many=True,
        context={'request': request}
    )
    
    return Response(serializer.data)


# apps/api/urls.py
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Authentication
    path('auth/login/', views.user_login, name='login'),
    path('auth/register/', views.user_register, name='register'),
    path('auth/logout/', views.user_logout, name='logout'),
    
    # Products
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('recommendations/', views.product_recommendations, name='recommendations'),
    path('recommendations/<int:product_id>/', views.product_recommendations, name='product_recommendations'),
    
    # Cart
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/items/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    
    # Wishlist
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Orders
    path('orders/', views.OrderListView.as_view(), name='orders'),
]