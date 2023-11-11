from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Store
from apps.core.models import Category
from django.db.models import Q
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from django.contrib import messages


def get_selected_categories(category_id):
    category = get_object_or_404(
        Category.objects.select_related("parent__parent__parent__parent"),
        pk=category_id
    )
    selected_categories = []
    while category:
        selected_categories.append(category)
        category = category.parent
    return reversed(selected_categories)


def store_view(request, store_id, category_slug=None):
    category_id = None
    selected_categories = []
    try:
        category_id, *_ = category_slug.split("-")
    except Exception:
        pass
    else:
        selected_categories = get_selected_categories(category_id)

    store = get_object_or_404(Store, pk=store_id)
    meta_description = store.name
    if selected_categories:
        meta_description = f"{meta_description}: {' '.join(c.name for c in selected_categories)}"

    search = request.GET.get("search", "").strip()
    if search:
        queryset = Product.get_search_queryset(search)
        meta_description = f"{meta_description} {search}"
    else:
        queryset = Product.objects.all()
    if category_id:
        queryset = queryset.filter(category__id__startswith=category_id)

    products = queryset.filter(store=store).filter(is_active=True).order_by('-created')

    paginator = Paginator(products, 18)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    child_categories = Category.objects.filter(parent_id=category_id)
    context = {
        'store': store,
        'products': paged_products,
        'product_count': paginator.count,
        'child_categories': child_categories,
        'selected_categories': selected_categories,
        'search': search,
        'meta_description': meta_description,
    }
    return render(request, 'store/store.html', context)


def product_details(request, store_id, product_slug):
    product = get_object_or_404(Product, store_id=store_id, slug=product_slug)

    # in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    # if request.user.is_authenticated:
    #     try:
    #         orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
    #     except OrderProduct.DoesNotExist:
    #         orderproduct = None
    # else:
    #     orderproduct = None

    if product.category_id is not None:
        selected_categories = get_selected_categories(product.category_id)
    else:
        selected_categories = []

    meta_description = f"{' '.join(c.name for c in selected_categories)} {product.name}"
    context = {
        'product': product,
        'in_cart': False,
        'selected_categories': selected_categories,
        'meta_description': meta_description,
    }
    return render(request, 'store/product.html', context)
    # return render(request, 'card/base.html', context)


# def search(request):
#     if 'keyword' in request.GET:
#         keyword = request.GET['keyword']
#         if keyword:
#             products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
#             product_count = products.count()
#     context = {
#         'products': products,
#         'product_count': product_count,
#     }
#     return render(request, 'store/store.html', context)
#
#
# def submit_review(request, product_id):
#     url = request.META.get('HTTP_REFERER')
#     if request.method == 'POST':
#         try:
#             reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
#             form = ReviewForm(request.POST, instance=reviews)
#             form.save()
#             messages.success(request, 'Thank you! Your review has been updated.')
#             return redirect(url)
#         except ReviewRating.DoesNotExist:
#             form = ReviewForm(request.POST)
#             if form.is_valid():
#                 data = ReviewRating()
#                 data.subject = form.cleaned_data['subject']
#                 data.rating = form.cleaned_data['rating']
#                 data.review = form.cleaned_data['review']
#                 data.ip = request.META.get('REMOTE_ADDR')
#                 data.product_id = product_id
#                 data.user_id = request.user.id
#                 data.save()
#                 messages.success(request, 'Thank you! Your review has been submitted.')
#                 return redirect(url)
