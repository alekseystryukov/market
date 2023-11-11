from django.db import models
from django.contrib.sessions.models import Session


# Create your models here.

class Cart(models.Model):
    created = models.DateField(auto_now_add=True)
    first_name = models.CharField(max_length=256, null=True, blank=True)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    phone = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        return f"Замовник {self.phone}"

    def update_customer_details(self, *_, phone, first_name, last_name):
        save = False
        if phone:
            self.phone = phone
            save = True
        if first_name:
            self.first_name = first_name
            save = True
        if last_name:
            self.last_name = last_name
            save = True
        if save:
            self.save()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, related_name="product_items")
    product = models.ForeignKey("store.Product", on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveSmallIntegerField(default=1)
    created = models.DateField(auto_now_add=True)

    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"Cart item: {self.product.name[:10]} x {self.quantity}"
