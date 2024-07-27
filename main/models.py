from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    category = models.CharField(max_length=10, choices=[('Bronze', 'Bronze'), ('Silver', 'Silver'), ('Gold', 'Gold')], default='Bronze')
    department = models.CharField(max_length=100, null=True, blank=True)

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.FloatField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category.name,
            'department': self.department,
        }

class Discount(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    customer_category = models.CharField(max_length=10, choices=[('Bronze', 'Bronze'), ('Silver', 'Silver'), ('Gold', 'Gold')])
    discount_percentage = models.FloatField()

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.FloatField()
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')

    def serialize(self):
        return {
            'id': self.id,
            'user': self.user.username,
            'total_price': self.total_price,
            'order_date': self.order_date,
            'status': self.status,
        }

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()