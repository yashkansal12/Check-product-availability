from django.contrib import admin
from .models import (
    Profile,
    Shop,
    Item,
    ItemRequest,
    CartItem,
    Transaction,
    Order,
    Wishlist,
    Recommendation,
)

# Register models
admin.site.register(Profile)
admin.site.register(Shop)
admin.site.register(Item)
admin.site.register(ItemRequest)
admin.site.register(CartItem)
admin.site.register(Transaction)
admin.site.register(Order)
admin.site.register(Wishlist)
admin.site.register(Recommendation)
