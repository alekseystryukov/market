from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.contrib.sitemaps.views import sitemap
from market.swagger import schema_view
from .views import home
from apps.store.urls import StoreSitemap
from django.views.generic import TemplateView

sitemaps = {
    "store": StoreSitemap
}

urlpatterns = [
    path("", home, name="home"),

    path('', include('apps.core.urls', namespace='core')),
    path('store/', include('apps.store.urls', namespace='store')),
    path('cart/', include('apps.cart.urls', namespace='cart')),
    path('', RedirectView.as_view(pattern_name='admin:index'), name='go-to-admin'),
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.SWAGGER_ENABLED:
    urlpatterns.append(
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')
    )

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(
        path('__debug__/', include(debug_toolbar.urls)),
    )
