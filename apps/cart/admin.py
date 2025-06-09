from django.contrib import admin
from .models import Cart, CartItem, Wishlist, WishlistItem, CompareList, CompareItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'total_items', 'total_price', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'session_key']
    readonly_fields = ['total_items', 'total_price', 'created_at', 'updated_at']
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'cart', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at']
    search_fields = ['product__name', 'cart__user__username']
    readonly_fields = ['total_price']


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'items_count', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
    inlines = [WishlistItemInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items Count'


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'wishlist', 'added_at']
    list_filter = ['added_at']
    search_fields = ['product__name', 'wishlist__user__username']


class CompareItemInline(admin.TabularInline):
    model = CompareItem
    extra = 0


@admin.register(CompareList)
class CompareListAdmin(admin.ModelAdmin):
    list_display = ['user', 'items_count', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CompareItemInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items Count'


@admin.register(CompareItem)
class CompareItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'compare_list', 'added_at']
    list_filter = ['added_at']
    search_fields = ['product__name', 'compare_list__user__username']