from django.shortcuts import render


def index(request):
    """Return the home page."""
    return render(request, "home/index.html")