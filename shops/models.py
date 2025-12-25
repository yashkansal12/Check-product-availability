from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# -------------------------
# Profile for Users
# -------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username


# -------------------------
# Shop Model
# -------------------------
class Shop(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="shop")
    shop_name = models.CharField(max_length=100)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.shop_name


# -------------------------
# Item / Product Model
# -------------------------
class Item(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="items")
    item_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    image = models.ImageField(upload_to='products/', blank=True, null=True)


    def __str__(self):
        return f"{self.name} ({self.shop.shop_name})"

class ItemRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=20, default="Pending")
    reply_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} -> {self.item_name}"


# -------------------------
# Cart Item (User's Cart)
# -------------------------
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Item, on_delete=models.CASCADE)  # Fixed: Item instead of Product
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"


# -------------------------
# Transaction / Sale
# -------------------------
class Transaction(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sales")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.username} bought {self.item.name} from {self.seller.username}"


# -------------------------
# Orders
# -------------------------
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("shipped", "Shipped"), ("delivered", "Delivered")],
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ Add this field
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ("cod", "Cash on Delivery"),
            ("upi", "UPI"),
            ("card", "Credit/Debit Card"),
            ("netbanking", "Net Banking"),
        ],
        default="cod"
    )

    def __str__(self):
        return f"Order: {self.user.username} - {self.item} ({self.status})"


# -------------------------
# Wishlist
# -------------------------
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} wishes {self.item.name}"


# -------------------------
# Recommendations
# -------------------------
class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.item.name}"


class Product(models.Model):
    product_name = models.CharField(max_length=200)
    shop_name = models.CharField(max_length=200)
    price = models.IntegerField()

    def __str__(self):
        return self.product_name
