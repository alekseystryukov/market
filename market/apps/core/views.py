import logging
from django.views.generic import TemplateView
from django.shortcuts import render
from apps.store.models import Product


logger = logging.getLogger(__name__)


def home(request):
    products = Product.objects.all().order_by('created')[:10]

    # Get the reviews
    reviews = None
    # for product in products:
    #     reviews = ReviewRating.objects.filter(product_id=product.id, status=True)

    context = {
        'products': products,
        'reviews': reviews,
    }
    return render(request, 'home.html', context)


class SuccessPageView(TemplateView):
    template_name = 'success_page.html'


class ErrorPageView(TemplateView):
    template_name = 'error_page.html'
