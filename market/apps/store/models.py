from apps.core.models import Category
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from uuid import uuid4
from datetime import datetime, timedelta
from django.core.serializers.json import DjangoJSONEncoder
import logging
import secrets
import string
import json

logger = logging.getLogger(__name__)


def get_store_media_destination(store_id):
    date = datetime.utcnow().isoformat().split("T")[0]
    return f"{settings.AWS_STORAGE_BUCKET_PREFIX}/media/{store_id}/{date}"


def logo_file_name(instance, filename):
    ext = filename.split('.')[-1]
    store_destination = get_store_media_destination(instance.id)
    return f"{store_destination}/{uuid4().hex}.{ext}"


class Store(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(max_length=1000, blank=True)
    logo = models.ImageField(upload_to=logo_file_name)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        kwargs = {
            'store_id': self.id,
        }
        return reverse('store:store', kwargs=kwargs)


def product_file_name(instance, filename):
    ext = filename.split('.')[-1]
    store_destination = get_store_media_destination(instance.store.id)
    return f"{store_destination}/{uuid4().hex}.{ext}"


class Product(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    slug = models.CharField(max_length=256)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=1000)
    description = models.TextField(max_length=5000, blank=True)  # https://pypi.org/project/django-ckeditor/
    price = models.DecimalField(max_digits=12, decimal_places=2)
    image = models.ImageField(upload_to=product_file_name)
    is_active = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        kwargs = {
            'store_id': self.store_id,
            'product_id': self.id,
            'product_slug': self.slug,
        }
        return reverse('store:product_details', kwargs=kwargs)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name[:256], allow_unicode=True)
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['slug'], name='product_slug_idx'),
            GinIndex(
                SearchVector("name", "description", config="russian"),  # TODO: add ukrainian instead
                name="search_vector_idx",
            )
        ]
        get_latest_by = "created"
        ordering = ['-created']

    @classmethod
    def get_search_queryset(cls, search):
        qs = cls.objects.annotate(
            search=SearchVector("name", "description"),  # GinIndex
        ).filter(search=search)
        return qs

    def get_json_ld(self):
        host_name = settings.CSRF_TRUSTED_ORIGINS[0] if settings.CSRF_TRUSTED_ORIGINS else ""
        result = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": self.name,
            "image": [
                i.file.url
                for i in self.images.all()
            ],
            "description": self.description,
            "sku": self.id,
            # "mpn": "925872",
            # "brand": {
            #     "@type": "Brand",
            #     "name": "ACME"
            # },
            # "review": {
            #     "@type": "Review",
            #     "reviewRating": {
            #         "@type": "Rating",
            #         "ratingValue": 4,
            #         "bestRating": 5
            #     },
            #     "author": {
            #         "@type": "Person",
            #         "name": "Fred Benson"
            #     }
            # },
            # "aggregateRating": {
            #     "@type": "AggregateRating",
            #     "ratingValue": 4.4,
            #     "reviewCount": 89
            # },
            "offers": {
                "@type": "Offer",
                "url": host_name + self.get_absolute_url(),
                "priceCurrency": "UAH",
                "price": self.price,
                "priceValidUntil": (datetime.now() + timedelta(days=5)).date().isoformat(),
                "itemCondition": "https://schema.org/UsedCondition",
                "availability": "https://schema.org/InStock"
            }
        }
        return json.dumps(result, cls=DjangoJSONEncoder, ensure_ascii=False)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    file = models.ImageField(upload_to=product_file_name)


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey('core.Attribute', on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=256)


def generate_order_id():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


ORDER_STATUS_CHOICES = [
    (0, "Створений"),
    (1, "Підтверджений"),
    (2, "Відправлений"),
    (3, "Отриманий"),
    (4, "Відмінений"),
]


class Order(models.Model):
    id = models.CharField(primary_key=True, max_length=32, default=generate_order_id)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='orders')
    cart = models.ForeignKey('cart.Cart', on_delete=models.CASCADE, related_name='orders')
    status = models.PositiveSmallIntegerField(choices=ORDER_STATUS_CHOICES, default=0, db_index=True)
    note = models.TextField(max_length=1000, blank=True)
    created = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def get_absolute_url(self):
        kwargs = {
            'order_id': self.id,
        }
        return reverse('cart:order_details', kwargs=kwargs)

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, related_name="product_items")
    product = models.ForeignKey("store.Product", on_delete=models.RESTRICT, related_name="order_items")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f"Order item: {self.product.name[:10]} x {self.quantity}"

