from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from apps.products.models import Product


class Cart(models.Model):
    """Shopping cart for each user session or authenticated user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("User"))
    session_key = models.CharField(max_length=50, null=True, blank=True, verbose_name=_("Session Key"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Cart for session {self.session_key}"

    @property
    def total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Get total price of all items in cart"""
        return sum(item.total_price for item in self.items.all())

    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """Individual items in a shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name=_("Cart"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("Product"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))
    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Added At"))

    class Meta:
        unique_together = ['cart', 'product']
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def total_price(self):
        """Get total price for this cart item"""
        return self.product.price * self.quantity


class Wishlist(models.Model):
    """User's wishlist"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _('Wishlist')
        verbose_name_plural = _('Wishlists')

    def __str__(self):
        return f"Wishlist for {self.user.username}"


class WishlistItem(models.Model):
    """Items in user's wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items', verbose_name=_("Wishlist"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("Product"))
    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Added At"))

    class Meta:
        unique_together = ['wishlist', 'product']
        verbose_name = _('Wishlist Item')
        verbose_name_plural = _('Wishlist Items')

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s wishlist"