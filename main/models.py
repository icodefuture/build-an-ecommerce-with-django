from django.db import models
from django.conf import settings
import os
import time

class Product(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, null=False)
    price = models.IntegerField()
    description = models.TextField(max_length=10000)
    image = models.ImageField(upload_to='media/products/', null=True, blank=True)

    def __str__(self):
        return self.title

def update_filename(instance, filename):
    path = "media/products/gallery/"
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (str(time.time()), ext)
    return os.path.join(path, filename)
    
class Gallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to=update_filename)

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_user")
    total = models.IntegerField(default=0)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_item")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_product")
    quantity = models.IntegerField()

    @property
    def total_cost(self):
        return self.quantity * self.product.price

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    total = models.IntegerField()
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20)
    city = models.CharField(max_length=40)
    country = models.CharField(max_length=40)
    line1 = models.CharField(max_length=150)
    line2 = models.CharField(max_length=150, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    status = models.CharField(max_length=20)
    session_id = models.CharField(max_length=100, null=True)
    payment_id = models.CharField(max_length=100, null=True)
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_item")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_product")
    quantity = models.IntegerField()

    @property
    def total_cost(self):
        return self.quantity * self.product.price