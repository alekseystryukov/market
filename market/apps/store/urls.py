from django.urls import path
from .views import store_view, product_details
from django.contrib.sitemaps import Sitemap
from .models import Product

app_name = "store"

urlpatterns = [
    path('<int:store_id>/', store_view, name='store'),
    path('<int:store_id>/category/<str:category_slug>/', store_view, name='store_category'),
    # path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('<int:store_id>/products/<str:product_slug>/', product_details, name='product_details'),
    # path('search/', views.search, name='search'),
    # path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
]


class StoreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.modified