# apps/recommendations/models.py
from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product

class UserBehavior(models.Model):
    """Track user behavior for recommendations"""
    
    ACTION_TYPES = [
        ('view', 'Product View'),
        ('cart_add', 'Add to Cart'),
        ('purchase', 'Purchase'),
        ('wishlist_add', 'Add to Wishlist'),
        ('search', 'Search'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=50, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    search_query = models.CharField(max_length=200, blank=True)
    
    # Context
    referrer = models.URLField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'action_type', 'created_at']),
            models.Index(fields=['product', 'action_type']),
            models.Index(fields=['session_key', 'created_at']),
        ]


class ProductSimilarity(models.Model):
    """Precomputed product similarity scores"""
    
    product_a = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similarities_a')
    product_b = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similarities_b')
    similarity_score = models.FloatField()
    
    # Different similarity types
    SIMILARITY_TYPES = [
        ('content', 'Content-based'),
        ('collaborative', 'Collaborative filtering'),
        ('hybrid', 'Hybrid approach'),
    ]
    similarity_type = models.CharField(max_length=20, choices=SIMILARITY_TYPES, default='content')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product_a', 'product_b', 'similarity_type']
        indexes = [
            models.Index(fields=['product_a', 'similarity_score']),
            models.Index(fields=['product_b', 'similarity_score']),
        ]


# apps/recommendations/services.py
import numpy as np
from django.db.models import Count, Q, F, Avg
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import pickle

class RecommendationEngine:
    """Advanced recommendation engine with multiple algorithms"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour
    
    def get_recommendations(self, user=None, product=None, session_key=None, limit=6, algorithm='hybrid'):
        """Get personalized recommendations"""
        
        cache_key = f"recommendations_{user.id if user else session_key}_{product.id if product else 'none'}_{algorithm}_{limit}"
        cached_recommendations = cache.get(cache_key)
        
        if cached_recommendations:
            return cached_recommendations
        
        recommendations = []
        
        if algorithm == 'content' or algorithm == 'hybrid':
            content_recs = self._content_based_recommendations(product, limit)
            recommendations.extend(content_recs)
        
        if algorithm == 'collaborative' or algorithm == 'hybrid':
            if user:
                collab_recs = self._collaborative_filtering_recommendations(user, limit)
                recommendations.extend(collab_recs)
        
        if algorithm == 'trending' or algorithm == 'hybrid':
            trending_recs = self._trending_recommendations(limit)
            recommendations.extend(trending_recs)
        
        # Remove duplicates and limit results
        seen_products = set()
        unique_recommendations = []
        
        for product_obj in recommendations:
            if product_obj.id not in seen_products:
                seen_products.add(product_obj.id)
                unique_recommendations.append(product_obj)
                
                if len(unique_recommendations) >= limit:
                    break
        
        # If we don't have enough, fill with popular products
        if len(unique_recommendations) < limit:
            popular_products = self._popular_products(limit - len(unique_recommendations))
            for product_obj in popular_products:
                if product_obj.id not in seen_products:
                    unique_recommendations.append(product_obj)
                    if len(unique_recommendations) >= limit:
                        break
        
        cache.set(cache_key, unique_recommendations, self.cache_timeout)
        return unique_recommendations
    
    def _content_based_recommendations(self, base_product, limit=6):
        """Content-based recommendations using product features"""
        
        if not base_product:
            return []
        
        # Get similar products from precomputed similarities
        similar_products = ProductSimilarity.objects.filter(
            Q(product_a=base_product) | Q(product_b=base_product),
            similarity_type='content'
        ).order_by('-similarity_score')[:limit * 2]
        
        recommendations = []
        for similarity in similar_products:
            similar_product = similarity.product_b if similarity.product_a == base_product else similarity.product_a
            if similar_product.is_available:
                recommendations.append(similar_product)
                if len(recommendations) >= limit:
                    break
        
        return recommendations
    
    def _collaborative_filtering_recommendations(self, user, limit=6):
        """Collaborative filtering based on user behavior"""
        
        # Find users with similar behavior
        user_products = UserBehavior.objects.filter(
            user=user,
            action_type__in=['purchase', 'cart_add', 'view']
        ).values_list('product_id', flat=True).distinct()
        
        if not user_products:
            return []
        
        # Find users who interacted with similar products
        similar_users = UserBehavior.objects.filter(
            product_id__in=user_products,
            action_type__in=['purchase', 'cart_add']
        ).exclude(user=user).values('user').annotate(
            common_products=Count('product', distinct=True)
        ).order_by('-common_products')[:20]
        
        similar_user_ids = [u['user'] for u in similar_users if u['user']]
        
        # Get products liked by similar users but not by current user
        recommended_products = UserBehavior.objects.filter(
            user_id__in=similar_user_ids,
            action_type__in=['purchase', 'cart_add']
        ).exclude(
            product_id__in=user_products
        ).values('product').annotate(
            score=Count('user', distinct=True)
        ).order_by('-score')[:limit]
        
        product_ids = [rp['product'] for rp in recommended_products]
        return Product.objects.filter(
            id__in=product_ids,
            is_active=True,
            is_in_stock=True
        ).select_related('category')[:limit]
    
    def _trending_recommendations(self, limit=6):
        """Get trending products based on recent activity"""
        
        cache_key = f"trending_products_{limit}"
        cached_trending = cache.get(cache_key)
        
        if cached_trending:
            return cached_trending
        
        # Products with high activity in last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        
        trending_products = UserBehavior.objects.filter(
            created_at__gte=week_ago,
            action_type__in=['view', 'cart_add', 'purchase']
        ).values('product').annotate(
            activity_score=Count('id') + Count('id', filter=Q(action_type='purchase')) * 5
        ).order_by('-activity_score')[:limit]
        
        product_ids = [tp['product'] for tp in trending_products if tp['product']]
        products = Product.objects.filter(
            id__in=product_ids,
            is_active=True,
            is_in_stock=True
        ).select_related('category')[:limit]
        
        cache.set(cache_key, list(products), 1800)  # Cache for 30 minutes
        return products
    
    def _popular_products(self, limit=6):
        """Get overall popular products"""
        
        cache_key = f"popular_products_{limit}"
        cached_popular = cache.get(cache_key)
        
        if cached_popular:
            return cached_popular
        
        # Products with high overall activity
        popular_products = UserBehavior.objects.filter(
            action_type__in=['view', 'cart_add', 'purchase']
        ).values('product').annotate(
            popularity_score=Count('id') + Count('id', filter=Q(action_type='purchase')) * 3
        ).order_by('-popularity_score')[:limit * 2]
        
        product_ids = [pp['product'] for pp in popular_products if pp['product']]
        products = Product.objects.filter(
            id__in=product_ids,
            is_active=True,
            is_in_stock=True
        ).select_related('category')[:limit]
        
        cache.set(cache_key, list(products), 3600)  # Cache for 1 hour
        return products
    
    def track_user_behavior(self, user=None, session_key=None, product=None, 
                          action_type='view', search_query='', request=None):
        """Track user behavior for future recommendations"""
        
        # Get request context
        referrer = ''
        ip_address = None
        user_agent = ''
        
        if request:
            referrer = request.META.get('HTTP_REFERER', '')[:500]
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        UserBehavior.objects.create(
            user=user,
            session_key=session_key,
            product=product,
            action_type=action_type,
            search_query=search_query,
            referrer=referrer,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SimilarityCalculator:
    """Calculate and update product similarities"""
    
    def calculate_content_similarities(self):
        """Calculate content-based similarities using TF-IDF"""
        
        products = Product.objects.filter(is_active=True).select_related('category')
        
        if products.count() < 2:
            return
        
        # Prepare text features
        product_texts = []
        product_objects = []
        
        for product in products:
            # Combine various text features
            text_features = [
                product.name or '',
                product.description or '',
                product.category.name or '',
                product.power or '',
                product.voltage or '',
                product.material or '',
                ' '.join([spec.name + ' ' + spec.value for spec in product.specifications.all()])
            ]
            
            combined_text = ' '.join(text_features).lower()
            product_texts.append(combined_text)
            product_objects.append(product)
        
        # Calculate TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = vectorizer.fit_transform(product_texts)
        
        # Calculate cosine similarities
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Store similarities in database
        ProductSimilarity.objects.filter(similarity_type='content').delete()
        
        similarities_to_create = []
        
        for i, product_a in enumerate(product_objects):
            for j, product_b in enumerate(product_objects):
                if i < j:  # Avoid duplicates and self-similarity
                    similarity_score = similarity_matrix[i][j]
                    
                    if similarity_score > 0.1:  # Only store meaningful similarities
                        similarities_to_create.append(
                            ProductSimilarity(
                                product_a=product_a,
                                product_b=product_b,
                                similarity_score=similarity_score,
                                similarity_type='content'
                            )
                        )
        
        # Batch create similarities
        ProductSimilarity.objects.bulk_create(similarities_to_create, batch_size=1000)
        
        print(f"Created {len(similarities_to_create)} content-based similarities")


# Management command: apps/recommendations/management/commands/update_similarities.py
from django.core.management.base import BaseCommand
from apps.recommendations.services import SimilarityCalculator

class Command(BaseCommand):
    help = 'Update product similarity calculations'
    
    def handle(self, *args, **options):
        calculator = SimilarityCalculator()
        calculator.calculate_content_similarities()
        self.stdout.write(
            self.style.SUCCESS('Successfully updated product similarities')
        )