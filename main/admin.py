from django.contrib import admin
from .models import User, Category, Product, Discount, Cart, Order, OrderItem

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'department']
    list_filter = ['category', 'department']
    search_fields = ['name', 'description']

class DiscountAdmin(admin.ModelAdmin):
    list_display = ['category', 'customer_category', 'discount_percentage']
    list_filter = ['category', 'customer_category']

admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(User)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
