from django.contrib import messages
from django.db.models import Q
from django.db.models.functions import Lower
from django.shortcuts import render, get_object_or_404, redirect

from .models import Product, Category


def all_products(request):
    """A view to show all products, including sorting, search queries and category filtering."""

    products = Product.objects.all()
    search_term = None
    current_categories = None
    sort = None
    direction = None

    if request.GET:
        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products = products.filter(category__name__in=categories)
            current_categories = Category.objects.filter(name__in=categories)

        if 'q' in request.GET:
            query = request.GET['q']

            if not query:
                messages.error(request, "You didn't enter any search criteria.")
                return redirect('products')

            queries = Q(name__icontains=query) | Q(description__icontains=query)
            products = products.filter(queries)
            search_term = query

        if 'sort' in request.GET:
            sortkey = request.GET['sort']
            sort = sortkey

            if sortkey == 'name':
                sortkey = 'lower_name'
                products = products.annotate(lower_name=Lower('name'))

            if sortkey == 'category':
                sortkey = 'category__name'

            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sortkey = f'-{sortkey}'

            products = products.order_by(sortkey)

    current_sorting = f'{sort}_{direction}'

    context = {
        'products': products,
        'search_term': search_term,
        'current_categories': current_categories,
        'current_sorting': current_sorting,
    }

    return render(request, 'products/products.html', context)


def product_detail(request, product_id):
    """A view to show individual product details."""
    product = get_object_or_404(Product, pk=product_id)

    context = {
        'product': product,
    }

    return render(request, 'products/product_detail.html', context)