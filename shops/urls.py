from django.urls import path
from . import views

app_name = "shops"

urlpatterns = [
    # Home and entry pages
    path('', views.home, name='home'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('checkout/', views.checkout, name='checkout'),


    path('user/', views.user_entry, name='user_entry'),
    path('shopkeeper/', views.shopkeeper_entry, name='shopkeeper_entry'),
  
    # User URLs
    path('user/register/', views.user_register, name='user_register'),
    path('user/login/', views.user_login, name='user_login'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user/profile/update/', views.update_profile, name='update_profile'),
   
    
    # Shopkeeper URLs
    path('shopkeeper/register/', views.shopkeeper_register, name='shopkeeper_register'),
    path('shopkeeper/login/', views.shopkeeper_login, name='shopkeeper_login'),
    path('shopkeeper/dashboard/', views.shopkeeper_dashboard, name='shopkeeper_dashboard'),
    path('shopkeeper/request/<int:request_id>/action/', views.handle_request_action, name='handle_request_action'),

    # Product
    
    path('send/request/<int:shop_id>/', views.send_request, name='send_request'),

    path('request/custom/<int:shop_id>/', views.request_custom_product, name='request_custom_product'),
    path('shopkeeper/<int:shop_id>/requests/', views.view_requests, name='view_requests'),
    path('user/requests/', views.user_requests, name='user_requests'),
    path('request/<int:request_id>/reply/', views.reply_request, name='reply_request'),

    path('product/edit/<int:item_id>/', views.edit_product, name='edit_product'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),

    # Buy items
    path('buy/<int:item_id>/', views.buy_item, name='buy_item'),
    path('shopkeeper/product/<int:item_id>/edit/', views.edit_product, name='edit_product'),
    path('shopkeeper/product/<int:item_id>/delete/', views.delete_product, name='delete_product'),
    path('user/wishlist/', views.wishlist_view, name='user_wishlist'),
    path('user/recommendations/', views.recommendation_view, name='recommendation'),
    path('user/close-account/', views.close_account_view, name='close_account'),
    path('place_order/', views.place_order, name='place_order'),
    path('order/confirmation/<str:order_ids>/', views.order_confirmation, name='order_confirmation'),
    path('order/<int:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path("cart/add/<int:item_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:order_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/", views.cart, name="cart"),

]
