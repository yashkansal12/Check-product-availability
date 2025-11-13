from django.db import models
from django.contrib.auth.models import User

# -------------------------
# Shop Model
# -------------------------
class Shop(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='shop_logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# -------------------------
# Product Availability Model
# -------------------------
class ProductAvailability(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=0)
    price = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.product_name} ({self.shop.name})"

# -------------------------
# Product Request Model
# -------------------------
class ProductRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} request by {self.user.username} ({self.status})"
