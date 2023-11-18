from django.shortcuts import render, redirect, get_object_or_404
from apps.store.models import Product, Order, OrderItem
from .models import Cart, CartItem
from .forms import OrderSubmitForm
from django.views.generic import TemplateView, FormView
from django.db.transaction import atomic
from django.core.mail import send_mail
from django.template import loader
from django.conf import settings
from django.urls import reverse
import logging


logger = logging.getLogger(__name__)

SESSION_CART_KEY = "cart_id"


def get_cart_id(request):
    cart_id = request.session.get(SESSION_CART_KEY)
    return cart_id


def set_cart_id(request, cart_id):
    request.session[SESSION_CART_KEY] = cart_id


def get_or_create_cart(request):
    cart_id = get_cart_id(request)
    if cart_id:
        try:
            obj = Cart.objects.get(pk=cart_id)
        except Cart.DoesNotExist:
            cart_id = None
    if not cart_id:
        obj = Cart.objects.create()
        set_cart_id(request, obj.pk)
    return obj


def add_product_view(request, product_id):
    if request.method != "POST":
        return redirect('home')

    product = get_object_or_404(Product, id=product_id)

    # get current cart
    cart_obj = get_or_create_cart(request)

    # add item to cart
    item, created = CartItem.objects.get_or_create(cart=cart_obj, product=product)
    if not created:
        quantity = int(request.POST.get("quantity"))
        if item.quantity != quantity:
            item.quantity = quantity
        else:
            item.quantity += 1
        item.save()
    return redirect('cart:cart')


def cart_view(request):
    # get current cart
    cart_obj = get_or_create_cart(request)
    cart_items = list(cart_obj.product_items.all().select_related("product")[:200])
    total = quantity = 0
    for item in cart_items:
        quantity += item.quantity
        total += item.quantity * item.product.price

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
    }
    return render(request, 'cart/cart.html', context)


def remove_item_view(request, item_id):
    cart_obj = get_or_create_cart(request)
    try:
        cart_item = cart_obj.product_items.get(id=item_id)
    except CartItem:
        pass
    else:
        cart_item.quantity -= 1
        if cart_item.quantity < 1:
            cart_item.delete()
        else:
            cart_item.save()
    return redirect('cart:cart')


def remove_product_view(request, product_id):
    cart_obj = get_or_create_cart(request)
    try:
        cart_item = cart_obj.product_items.get(product_id=product_id)
    except CartItem:
        pass
    else:
        cart_item.delete()
    return redirect('cart:cart')


class PlaceOrderView(FormView):
    template_name = "cart/order.html"
    form_class = OrderSubmitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_obj = get_or_create_cart(self.request)
        cart_items = list(cart_obj.product_items.all().select_related("product")[:200])
        store_id = cart_items[0].product.store_id if cart_items else None
        total = quantity = 0
        for item in cart_items:
            quantity += item.quantity
            total += item.quantity * item.product.price

        if self.request.method == "GET":
            pass
        context.update({
            'total': total,
            'quantity': quantity,
            'cart': cart_obj,
            'cart_items': cart_items,
            'store_id': store_id,
        })
        return context

    def get_initial(self):
        initial = super().get_initial()
        cart_obj = get_or_create_cart(self.request)
        initial['phone'] = cart_obj.phone
        initial['first_name'] = cart_obj.first_name
        initial['last_name'] = cart_obj.last_name
        return initial

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            data = form.clean()
            cart_obj = get_or_create_cart(self.request)
            cart_obj.update_customer_details(
                phone=data["phone"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )

            store_id = data["store_id"]
            store_items = cart_obj.product_items.filter(product__store=store_id)
            cart_items = list(store_items.select_related("product")[:200])
            total = sum(item.quantity * item.product.price for item in cart_items)
            if cart_items:
                with atomic():
                    order = Order.objects.create(
                        store_id=data["store_id"],
                        cart=cart_obj,
                        note=data["note"],
                        total=total,
                    )
                    order_items = OrderItem.objects.bulk_create([
                        OrderItem(
                            order=order,
                            product=i.product,
                            price=i.product.price,
                            quantity=i.quantity,
                        )
                        for i in cart_items
                    ])
                    store_items.delete()

                order_url = request.build_absolute_uri(
                    reverse('cart:order_details', kwargs=dict(order_id=order.id))
                )
                store_user_emails = order.store.users.all().values_list("email", flat=True)
                if not store_user_emails:
                    logger.error(f"{order.store} has not managers")
                else:
                    html_message = loader.render_to_string(
                        'cart/order_email.html',
                        dict(
                            order=order,
                            order_url=order_url,
                            order_admit_url=request.build_absolute_uri(
                                reverse('admin:store_order_change', kwargs=dict(object_id=order.id))
                            ),
                            order_items=order_items,
                        )
                    )
                    r = send_mail(
                        subject=f"New order #{order.id[:4]}",
                        message=f"\nYou have a new order {order_url}",
                        html_message=html_message,
                        from_email=settings.EMAIL_NO_REPLY_FROM,
                        recipient_list=store_user_emails,
                        fail_silently=False,
                    )
                return redirect(order_url)
            return redirect('home')
        return self.form_invalid(form)


def order_detail_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order_items = list(order.product_items.all().select_related("product")[:200])
    total = quantity = 0
    for item in order_items:
        quantity += item.quantity
        total += item.quantity * item.product.price
    context = {
        'order': order,
        'total': total,
        'quantity': quantity,
        'order_items': order_items,
    }
    return render(request, 'cart/order_detail.html', context)