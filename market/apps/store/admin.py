from django.contrib import admin
from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import Store, Product, ProductImage, Order, OrderItem
import logging

logger = logging.getLogger(__name__)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    list_display = ("file",)
    extra = 0


class ProductAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Product
        fields = '__all__'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'store')
    inlines = [ProductImageInline]
    form = ProductAdminForm

    list_select_related = (
        'category', 'store',
    )
    list_filter = ["store", "category"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    list_display = ("product", "price", "quantity")
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created')
    fields = ("id", "created", "total", "status")
    readonly_fields = ("id", "created", "total")
    list_filter = ["status"]

    inlines = [OrderItemInline]

    change_form_template = 'admin/store/order_change_form.html'




