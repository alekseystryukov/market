from .models import CartItem
from .views import get_cart_id


def cart_counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        cart_id = get_cart_id(request)
        if cart_id:
            cart_count = CartItem.objects.filter(cart_id=cart_id).count()
    return dict(cart_count=cart_count)
