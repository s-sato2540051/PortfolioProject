from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db.models import Count

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
            portfolio.save()  # まず保存してPKを取得
            
            # タグの処理 - set()の代わりに文字列をそのまま渡す
            tags_data = request.POST.get('tags', '')
            print(f"DEBUG - tags_data from POST: {tags_data}")  # デバッグ用
            
            if tags_data:
                # taggitは "tag1, tag2, tag3" の形式を受け付ける
                portfolio.tags.add(*[tag.strip() for tag in tags_data.split(',') if tag.strip()])
            
            return redirect("my_page")
    else:
        form = PortfolioForm()
    
    # 使用頻度順にタグを取得
    popular_tags = Tag.objects.annotate(
        usage_count=Count('taggit_taggeditem_items')
    ).filter(usage_count__gt=0).order_by('-usage_count', 'name')[:50]
    
    return render(request, "portfolio_create.html", {
        "form": form,
        "popular_tags": popular_tags
    })


def logout_view(request):
    logout(request)
    return redirect('home')