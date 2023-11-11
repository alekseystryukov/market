from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path('', views.cart_view, name='cart'),
    path('add_product/<str:product_id>/', views.add_product_view, name='add_product'),
    path('remove_cart_item/<str:item_id>/', views.remove_item_view, name='remove_item'),
    path('remove_cart_product/<str:product_id>/', views.remove_product_view, name='remove_product'),
    path('order/', views.PlaceOrderView.as_view(), name='order'),
    path('order/<str:order_id>/', views.order_detail_view, name='order_details'),
]
