from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.http import FileResponse
from .models import Profile, Shop, Item, ItemRequest, Transaction, Order, Wishlist, Recommendation


# ---------------- Home & Entry Pages ----------------
def home(request):
    return render(request, 'shops/home.html')

def user_entry(request):
    return render(request, 'shops/user_entry.html')

def shopkeeper_entry(request):
    return render(request, 'shops/shopkeeper_entry.html')

def custom_logout(request):
    logout(request)
    return redirect('shops:home')

# ---------------- USER Register/Login ----------------
def user_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        phone = request.POST.get("phone")
        address = request.POST.get("address", "")

        # check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Username already exists")
            return redirect("shops:user_register")

        # create user
        user = User.objects.create_user(username=username, password=password)

        # create or update profile
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={"phone": phone, "address": address}
        )
        if not created:
            profile.phone = phone
            profile.address = address
            profile.save()

        messages.success(request, "✅ User registered successfully! Please log in.")
        return redirect("shops:user_login")

    return render(request, "shops/user_register.html")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("shops:user_dashboard")
        else:
            messages.error(request, "❌ Invalid credentials")

    return render(request, "shops/user_login.html")


@login_required
def user_dashboard(request):
    user = request.user
    profile = user.profile

    # ---- Handle AJAX inline profile update ----
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        field = request.POST.get("field")
        value = request.POST.get("value")

        # Map JS fields to model fields
        field_mapping = {
            "username": "username",
            "email": "email",
            "mobile": "phone",
            "address": "address",
            "password": "password"
        }

        if field not in field_mapping:
            return JsonResponse({"success": False, "error": "Invalid field"})

        try:
            if field == "username":
                user.username = value
            elif field == "email":
                user.email = value
            elif field == "mobile":
                profile.phone = value
            elif field == "address":
                profile.address = value
            elif field == "password":
                user.set_password(value)
                update_session_auth_hash(request, user)  # keep user logged in

            user.save()
            profile.save()
            return JsonResponse({"success": True, "field": field, "value": value})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    # ---- Normal GET request: render dashboard ----
    shops = Shop.objects.prefetch_related("items").all()
    requests = ItemRequest.objects.filter(user=user).select_related("shop", "item")
    orders = Order.objects.filter(user=user).order_by("-id")

    return render(request, "shops/user_dashboard.html", {
        "shops": shops,
        "requests": requests,
        "orders": orders,
        "profile": profile
    })

@login_required
def update_profile(request):
    if request.method == "POST":
        user = request.user
        profile = user.profile

        field = request.POST.get("field")
        value = request.POST.get("value")

        try:
            if field == "username":
                user.username = value
            elif field == "email":
                user.email = value
            elif field == "mobile":
                profile.phone = value
            elif field == "password":
                user.set_password(value)
                update_session_auth_hash(request, user)  # keep user logged in
            elif field == "address":
                profile.address = value
            else:
                return JsonResponse({"success": False, "error": "Invalid field"})

            user.save()
            profile.save()
            return JsonResponse({"success": True, "field": field, "value": value})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

# ---------------- SHOPKEEPER Register/Login ----------------
def shopkeeper_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        shop_name = request.POST.get("shop_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address", "")

        if User.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Username already taken")
            return redirect("shops:shopkeeper_register")

        # Create user
        user = User.objects.create_user(username=username, password=password)

        # Create or update Profile
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={"phone": phone, "address": address}
        )
        if not created:
            profile.phone = phone
            profile.address = address
            profile.save()

        # Create Shop
        Shop.objects.create(user=user, shop_name=shop_name, address=address)

        messages.success(request, "✅ Shopkeeper registered successfully! Please log in.")
        return redirect("shops:shopkeeper_login")

    return render(request, "shops/shopkeeper_register.html")


@login_required
def shopkeeper_dashboard(request):
    try:
        shop = request.user.shop
    except Shop.DoesNotExist:
        messages.error(request, "⚠️ You don’t have a shop linked to this account.")
        return redirect("shops:home")

    # ---- Fetch all items (no pagination) ----
    items = Item.objects.filter(shop=shop).order_by('-item_id')

    # ---- Fetch requests and transactions ----
    requests = ItemRequest.objects.filter(shop=shop).order_by("-created_at")
    sold_transactions = Transaction.objects.filter(
        seller=request.user
    ).select_related("item", "buyer").order_by("-date")

    # ---- Handle Profile + Shop update ----
    if request.method == "POST" and "update_profile" in request.POST:
        user = request.user
        profile = user.profile
        shop = user.shop 

        user.username = request.POST.get("username", user.username)
        user.email = request.POST.get("email", user.email)
        shop.shop_name = request.POST.get("shop_name", shop.shop_name)
        profile.phone = request.POST.get("phone", profile.phone)
        profile.address = request.POST.get("address", profile.address)

        user.save()
        shop.save()
        profile.save()
        messages.success(request, "✅ Profile & Shop updated successfully!")
        return redirect("shops:shopkeeper_dashboard")

    # ---- Handle adding new product ----
    if request.method == "POST" and "add_product" in request.POST:
        name = request.POST.get("name")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")
        description = request.POST.get("description", "")

        try:
            if name and quantity and price:
                Item.objects.create(
                    shop=shop,
                    name=name,
                    quantity=int(quantity),
                    price=float(price),
                    description=description,
                )
                messages.success(request, "✅ Product added successfully!")
            else:
                messages.error(request, "⚠️ Please fill required fields.")
        except ValueError:
            messages.error(request, "⚠️ Invalid number format for price/quantity.")
        return redirect("shops:shopkeeper_dashboard")

    # ---- Handle AJAX request for user request approve/reject ----
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        request_id = request.POST.get("request_id")
        action = request.POST.get("action")
        reply_message = request.POST.get("reply_message", "")

        try:
            item_request = ItemRequest.objects.get(id=request_id, shop=shop)
            if action == "approve":
                item_request.status = "Approved"
            elif action == "reject":
                item_request.status = "Rejected"
            else:
                return JsonResponse({"success": False, "error": "Invalid action."})

            item_request.reply_message = reply_message
            item_request.save()

            return JsonResponse({"success": True, "status": item_request.status})
        except ItemRequest.DoesNotExist:
            return JsonResponse({"success": False, "error": "Request not found."})

    return render(request, "shops/shopkeeper_dashboard.html", {
        "shop": shop,
        "items": items,  # all items, no pagination
        "requests": requests,
        "sold_transactions": sold_transactions,
    })



def shopkeeper_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # You can also check if the user is a shopkeeper using groups or a custom field
            login(request, user)
            return redirect("shops:shopkeeper_dashboard")  # redirect to dashboard
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "shops/shopkeeper_login.html")


@login_required
def edit_product(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    if request.method == "POST":
        # Update fields safely
        item.name = request.POST.get("name", item.name)
        item.description = request.POST.get("description", item.description)

        quantity = request.POST.get("quantity")
        price = request.POST.get("price")

        if quantity is not None and quantity != "":
            try:
                item.quantity = int(quantity)
            except ValueError:
                pass  # keep old value if invalid

        if price is not None and price != "":
            try:
                item.price = float(price)
            except ValueError:
                pass  # keep old value if invalid

        item.save()

        # Return JSON for AJAX requests
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "id": item.item_id,
                "name": item.name,
                "description": item.description or "",
                "quantity": item.quantity,
                "price": str(item.price)  # keep as string for JS
            })

        return redirect("shops:shopkeeper_dashboard")

    return JsonResponse({"success": False})

@login_required
def delete_product(request, item_id):
    product = get_object_or_404(Item, pk=item_id)
    if request.user != product.shop.user:
        return HttpResponse("❌ Forbidden", status=403)
    if request.method == "POST":
        product.delete()
        messages.success(request, "✅ Product deleted successfully")
        return redirect("shops:shopkeeper_dashboard")
    return render(request, "shops/delete_product.html", {"item": product})

@login_required
def send_request(request, shop_id, item_id=None):
    shop = get_object_or_404(Shop, id=shop_id)

    if request.method == "POST":
        quantity = request.POST.get("quantity", 1)
        message = request.POST.get("message", "")
        
        # If it's for a specific item (user clicked "Request this item")
        if item_id:
            item = get_object_or_404(Item, id=item_id, shop=shop)
            ItemRequest.objects.create(
                user=request.user,
                shop=shop,
                item=item,
                item_name=item.name,  # keep for backup
                quantity=quantity,
                reply_message=message,
            )
        else:
            # Custom request (no existing product)
            custom_name = request.POST.get("item_name", "Custom Item")
            ItemRequest.objects.create(
                user=request.user,
                shop=shop,
                item_name=custom_name,
                quantity=quantity,
                reply_message=message,
            )

        messages.success(request, "✅ Request sent successfully!")
        return redirect("shops:user_requests")

    return redirect("shops:shop_detail", shop_id=shop.id)


# ---------------- Wishlist & Recommendations ----------------
@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user)
    return render(request, "shops/user_wishlist.html", {"items": items})


@login_required
def recommendation_view(request):
    recommendations = Recommendation.objects.filter(user=request.user)
    return render(request, "shops/recommendation.html", {"recommendations": recommendations})


@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    quantity = int(request.POST.get('quantity', 1))

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=item,
        defaults={'quantity': quantity}
    )
    if not created:
        # If item already in cart, just update quantity
        cart_item.quantity += quantity
        cart_item.save()

    return redirect('shops:user_dashboard')  # or redirect to cart page


@login_required
def close_account_view(request):
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "✅ Your account has been closed permanently.")
        return redirect("shops:home")

    return render(request, "shops/close_account_confirm.html")

@login_required
def request_custom_product(request, shop_id):
    """
    Allow a logged-in user to request a custom product from a shopkeeper.
    """
    shop = get_object_or_404(Shop, id=shop_id)

    if request.method == "POST":
        # Requesting based on existing item (optional)
        item_id = request.POST.get("item_id")
        custom_name = request.POST.get("custom_name", "").strip()
        quantity = request.POST.get("quantity", 1)

        item = None
        item_name = custom_name

        if item_id:
            item = get_object_or_404(Item, id=item_id, shop=shop)
            item_name = item.name  # use actual product name

        if not item and not custom_name:
            messages.error(request, "⚠️ Please specify an existing item or enter a custom product name.")
            return redirect("shops:shop_detail", shop_id=shop.id)

        ItemRequest.objects.create(
            user=request.user,
            shop=shop,
            item=item,
            item_name=item_name,
            quantity=quantity,
        )

        messages.success(request, "✅ Your request has been sent to the shopkeeper.")
        return redirect("shops:shop_detail", shop_id=shop.id)

    messages.error(request, "⚠️ Invalid request.")
    return redirect("shops:home")


@login_required
def view_requests(request, shop_id):
    """
    Shopkeeper: View all requests for their shop.
    """
    shop = get_object_or_404(Shop, id=shop_id)

    if request.user != shop.user:
        messages.error(request, "⚠️ You are not authorized to view these requests.")
        return redirect("shops:home")

    requests_qs = ItemRequest.objects.filter(shop=shop).select_related("user", "item").order_by('-created_at')

    return render(request, "shops/view_requests.html", {
        "shop": shop,
        "requests": requests_qs
    })


@login_required
def reply_request(request, request_id):
    """
    Shopkeeper: Approve/Reject and/or reply to a user request.
    Supports AJAX.
    """
    item_request = get_object_or_404(ItemRequest, id=request_id)
    if request.user != item_request.shop.user:
        if request.is_ajax():
            return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)
        messages.error(request, "⚠️ You are not authorized to update this request.")
        return redirect("shops:home")

    if request.method == "POST":
        status = request.POST.get("status")
        reply_message = request.POST.get("reply_message", "").strip()

        if status in ["Pending", "Approved", "Rejected"]:
            item_request.status = status
        if reply_message:
            item_request.reply_message = reply_message

        item_request.save()

        if request.is_ajax():
            return JsonResponse({
                "success": True,
                "status": item_request.status,
                "reply_message": item_request.reply_message
            })
        else:
            messages.success(request, "✅ Request updated successfully.")
            return redirect("shops:view_requests", shop_id=item_request.shop.id)

    # If GET, redirect to view requests
    return redirect("shops:view_requests", shop_id=item_request.shop.id)


@login_required
def user_requests(request):
    """
    Customer: view their own submitted requests.
    """
    requests = ItemRequest.objects.filter(user=request.user).select_related("shop", "item")

    return render(request, "shops/user_requests.html", {
        "requests": requests
    })

@login_required
def buy_item(request, item_id):
    """
    Add a single item to a temporary checkout order and redirect to checkout page.
    """
    item = get_object_or_404(Item, pk=item_id)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (ValueError, TypeError):
            messages.error(request, "⚠️ Invalid quantity.")
            return redirect("shops:user_dashboard")

        if quantity <= 0:
            messages.error(request, "⚠️ Quantity must be at least 1.")
            return redirect("shops:user_dashboard")

        if quantity > item.quantity:
            messages.error(request, f"❌ Only {item.quantity} items available.")
            return redirect("shops:user_dashboard")

        # Create a pending Order (status="Pending")
        Order.objects.create(
            user=request.user,
            item=item,
            quantity=quantity,
            total_price=item.price * quantity,
            status="Pending",
            created_at=datetime.datetime.now()
        )

        messages.success(request, f"✅ {quantity} × {item.name} added to checkout.")
        return redirect("shops:checkout")

    return redirect("shops:user_dashboard")

from django.utils import timezone  
from django.views.decorators.csrf import csrf_exempt
import io
from django.template.loader import render_to_string
from xhtml2pdf import pisa

@login_required
def checkout(request):
    """
    Checkout page: display orders, shipping info, handle AJAX updates, and place order.
    """
    user = request.user
    profile = user.profile
    orders = Order.objects.filter(user=user, status="Pending")
    total_amount = sum(o.total_price for o in orders)

    # ---------------- AJAX updates (quantity change / remove item) ----------------
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        action = request.POST.get("action")
        order_id = request.POST.get("order_id")
        order = get_object_or_404(Order, id=order_id, user=user)

        if action == "update_quantity":
            try:
                quantity = int(request.POST.get("quantity", order.quantity))
                if quantity <= 0:
                    return JsonResponse({"success": False, "error": "Quantity must be at least 1."})
                elif quantity > order.item.quantity + order.quantity:
                    return JsonResponse({"success": False, "error": "Not enough stock available."})

                # Adjust total price and quantity
                order.item.quantity += order.quantity - quantity
                order.quantity = quantity
                order.total_price = order.quantity * order.item.price
                order.item.save()
                order.save()

                return JsonResponse({
                    "success": True,
                    "order_id": order.id,
                    "quantity": order.quantity,
                    "subtotal": order.total_price,
                    "total_amount": sum(o.total_price for o in Order.objects.filter(user=user, status="Pending"))
                })
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid quantity."})

        elif action == "remove_order":
            order.item.quantity += order.quantity
            order.item.save()
            order.delete()
            return JsonResponse({
                "success": True,
                "order_id": order_id,
                "total_amount": sum(o.total_price for o in Order.objects.filter(user=user, status="Pending"))
            })

    # ---------------- Normal POST request (Place Order) ----------------
    if request.method == "POST" and not request.headers.get("x-requested-with"):
        if not orders.exists():
            messages.warning(request, "⚠️ No items in your cart to place order.")
            return redirect("shops:user_dashboard")

        new_address = request.POST.get("address")
        if new_address:
            profile.address = new_address
            profile.save()

        payment_method = request.POST.get("payment_method", "COD")
        processed_order_ids = []

        for order in orders:
            order.status = "Paid"
            order.payment_method = payment_method
            order.paid_at = timezone.now()
            order.save()
            processed_order_ids.append(str(order.id))

            # Reduce stock
            order.item.quantity -= order.quantity
            order.item.save()

            # Create Transaction for each order
            Transaction.objects.create(
                buyer=user,
                seller=order.item.shop.user,
                item=order.item,
                quantity=order.quantity,
                total_price=order.total_price
            )

        messages.success(request, "✅ Payment successful! Your orders are confirmed.")
        return redirect("shops:order_confirmation", order_ids=",".join(processed_order_ids))

    # ---------------- Normal page load ----------------
    return render(request, "shops/checkout.html", {
        "user": user,
        "profile": profile,
        "orders": orders,
        "total_amount": total_amount,
    })

@login_required
def place_order(request):
    """
    Handles order placement from other flows.
    Creates Transaction entries for each order.
    """
    user = request.user
    profile = user.profile
    orders = Order.objects.filter(user=user, status="Pending")

    if not orders.exists():
        messages.warning(request, "⚠️ No items in your cart to place order.")
        return redirect("shops:user_dashboard")

    if request.method == "POST":
        new_address = request.POST.get("address")
        if new_address:
            profile.address = new_address
            profile.save()

        payment_method = request.POST.get("payment_method", "COD")
        processed_order_ids = []

        for order in orders:
            order.status = "Paid"
            order.paid_at = timezone.now()
            order.payment_method = payment_method
            order.save()
            processed_order_ids.append(str(order.id))

            # Reduce stock
            order.item.quantity -= order.quantity
            order.item.save()

            # Create Transaction for each order
            Transaction.objects.create(
                buyer=user,
                seller=order.item.shop.user,
                item=order.item,
                quantity=order.quantity,
                total_price=order.total_price
            )

        messages.success(request, "✅ Your order has been placed successfully!")
        return redirect("shops:order_confirmation", order_ids=",".join(processed_order_ids))

    return redirect("shops:checkout")


@login_required
def order_confirmation(request, order_ids):
    """
    Displays a stylish order confirmation page.
    """
    ids = [int(i) for i in order_ids.split(",")]
    orders = Order.objects.filter(id__in=ids, user=request.user)
    total_amount = sum(o.total_price for o in orders)

    return render(request, "shops/order_confirmation.html", {
        "orders": orders,
        "total_amount": total_amount,
        "user": request.user,
        "profile": request.user.profile,
    })

@login_required
def download_invoice(request, order_id):
    """Generate PDF invoice for an order"""
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Invoice Header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, height - 50, "INVOICE")

    # Order Info
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Invoice No: {order.id}")
    p.drawString(50, height - 120, f"Customer: {order.user.username}")
    p.drawString(50, height - 140, f"Shop: {order.item.shop.shop_name}")
    p.drawString(50, height - 160, f"Item: {order.item.name}")
    p.drawString(50, height - 180, f"Quantity: {order.quantity}")
    p.drawString(50, height - 200, f"Total Price: ₹{order.total_price}")
    p.drawString(50, height - 220, f"Payment Method: {order.payment_method}")
    p.drawString(50, height - 240, f"Order Date: {order.created_at.strftime('%d-%m-%Y %H:%M')}")

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 50, "Thank you for shopping with us!")

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"invoice_{order.id}.pdf")


@login_required
def add_to_cart(request, item_id):
    """
    Add a product to the cart (Pending orders).
    If item already in cart → increase quantity.
    """
    item = get_object_or_404(Item, pk=item_id)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (ValueError, TypeError):
            messages.error(request, "⚠️ Invalid quantity.")
            return redirect("shops:user_dashboard")

        if quantity <= 0:
            messages.error(request, "⚠️ Quantity must be at least 1.")
            return redirect("shops:user_dashboard")

        if quantity > item.quantity:
            messages.error(request, f"❌ Only {item.quantity} items available.")
            return redirect("shops:user_dashboard")

        # Check if already in cart (Pending order)
        order, created = Order.objects.get_or_create(
            user=request.user,
            item=item,
            status="Pending",
            defaults={"quantity": quantity, "total_price": item.price * quantity}
        )

        if not created:
            order.quantity += quantity
            order.total_price = order.quantity * item.price
            order.save()

        messages.success(request, f"✅ {quantity} × {item.name} added to your cart.")
        return redirect("shops:cart")  # go to cart page

    return redirect("shops:user_dashboard")

@login_required
def remove_from_cart(request, order_id):
    """
    Remove a product from the cart.
    """
    order = get_object_or_404(Order, pk=order_id, user=request.user, status="Pending")
    order.delete()
    messages.info(request, "🗑️ Item removed from your cart.")
    return redirect("shops:checkout")

@login_required
def cart(request):
    """
    Cart page with AJAX quantity update & remove.
    """
    user = request.user
    cart_items = Order.objects.filter(user=user, status="Pending")
    total_amount = sum(o.total_price for o in cart_items)

    # Handle AJAX requests
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        action = request.POST.get("action")
        order_id = request.POST.get("order_id")
        order = get_object_or_404(Order, id=order_id, user=user)

        if action == "update_quantity":
            try:
                quantity = int(request.POST.get("quantity", order.quantity))
                if quantity <= 0:
                    return JsonResponse({"success": False, "error": "Quantity must be at least 1."})
                elif quantity > order.item.quantity + order.quantity:
                    return JsonResponse({"success": False, "error": "Not enough stock available."})

                # Adjust stock & price
                order.item.quantity += order.quantity - quantity
                order.quantity = quantity
                order.total_price = order.quantity * order.item.price
                order.item.save()
                order.save()

                return JsonResponse({
                    "success": True,
                    "order_id": order.id,
                    "quantity": order.quantity,
                    "subtotal": order.total_price,
                    "total_amount": sum(o.total_price for o in Order.objects.filter(user=user, status="Pending"))
                })
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid quantity."})

        elif action == "remove_order":
            order.item.quantity += order.quantity
            order.item.save()
            order.delete()
            return JsonResponse({
                "success": True,
                "order_id": order_id,
                "total_amount": sum(o.total_price for o in Order.objects.filter(user=user, status="Pending"))
            })

    return render(request, "shops/cart.html", {
        "cart_items": cart_items,
        "total_amount": total_amount,
    })

@login_required
def handle_request_action(request, request_id):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        item_request = get_object_or_404(ItemRequest, id=request_id, shop=request.user.shop)
        action = request.POST.get("action")
        reply = request.POST.get("reply", "")

        if action in ["approve", "reject"]:
            item_request.status = "Approved" if action == "approve" else "Rejected"
            item_request.reply_message = reply
            item_request.save()

            return JsonResponse({
                "success": True,
                "status": item_request.status,
                "reply_message": item_request.reply_message
            })
        return JsonResponse({"success": False, "error": "Invalid action"})
    return JsonResponse({"success": False, "error": "Invalid request"})