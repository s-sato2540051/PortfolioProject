from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from .models import Portfolio
from .forms import PortfolioForm

from taggit.models import Tag  


def home(request):
    portfolios = Portfolio.objects.filter(is_public=True).order_by("-created_at")[:10]
    return render(request, "home.html", {"portfolios": portfolios})


@login_required
def my_page(request):
    portfolios = Portfolio.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "my_page.html", {"portfolios": portfolios})


def portfolio_detail(request, pk):
    p = get_object_or_404(Portfolio, pk=pk)
    return render(request, "portfolio_detail.html", {"portfolio": p})


@login_required
def portfolio_create(request):
    if request.method == "POST":
        form = PortfolioForm(request.POST, request.FILES)
        if form.is_valid():
            portfolio = form.save(commit=False)
            portfolio.user = request.user
            portfolio.save()
            form.save_m2m()  
            return redirect("my_page")
    else:
        form = PortfolioForm()

    return render(request, "portfolio_create.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('home')

