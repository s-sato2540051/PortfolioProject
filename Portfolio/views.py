from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db.models import Count
import json

from .models import Portfolio, PortfolioImage, CoAuthor
from .forms import PortfolioForm
from taggit.models import Tag


def home(request):
    portfolios = Portfolio.objects.filter(is_public=True).order_by("-created_at")[:10]
    return render(request, "home.html", {"portfolios": portfolios})


@login_required
def my_page(request):
    portfolios = Portfolio.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "my_page.html", {"portfolios": portfolios})


def user_page(request, username):
    """他のユーザーのページを表示"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = get_object_or_404(User, username=username)
    
    # 自分のページなら my_page にリダイレクト
    if request.user.is_authenticated and request.user.username == username:
        return redirect('my_page')
    
    # 公開作品のみ表示
    portfolios = Portfolio.objects.filter(user=user, is_public=True).order_by("-created_at")
    
    return render(request, "user_page.html", {
        "page_user": user,
        "portfolios": portfolios
    })


def portfolio_detail(request, pk):
    p = get_object_or_404(Portfolio, pk=pk)
    
    # 共同制作者の外部アカウントを整形
    coauthors_processed = []
    for coauthor in p.coauthors.all():
        if coauthor.user:
            coauthors_processed.append({
                'type': 'internal',
                'user': coauthor.user
            })
        else:
            # 外部アカウントを分割
            if '|' in coauthor.ex_account:
                name, url = coauthor.ex_account.split('|', 1)
                
                # URLからアイコンを判定
                icon = 'bi-link-45deg'
                icon_color = ''
                if 'twitter.com' in url or 'x.com' in url:
                    icon = 'bi-twitter-x'
                elif 'youtube.com' in url or 'youtu.be' in url:
                    icon = 'bi-youtube'
                    icon_color = 'color: #FF0000;'
                
                coauthors_processed.append({
                    'type': 'external',
                    'name': name,
                    'url': url,
                    'icon': icon,
                    'icon_color': icon_color
                })
            else:
                coauthors_processed.append({
                    'type': 'external_simple',
                    'name': coauthor.ex_account
                })
    
    return render(request, "portfolio_detail.html", {
        "portfolio": p,
        "coauthors_processed": coauthors_processed
    })


@login_required
def portfolio_create(request):
    if request.method == "POST":
        form = PortfolioForm(request.POST, request.FILES)
        if form.is_valid():
            portfolio = form.save(commit=False)
            portfolio.user = request.user
            portfolio.save() 
            
            #タグの処理
            tags_data = form.cleaned_data.get('tags', '')
            if tags_data:
                tags_data = tags_data.replace("'", "").replace('"', '').replace('[', '').replace(']', '')
                tag_list = [tag.strip() for tag in tags_data.split(',') if tag.strip()]
                
                for tag in tag_list:
                    portfolio.tags.add(tag)
            
            for i in range(1, 5):
                image = form.cleaned_data.get(f'image{i}')
                if image:
                    PortfolioImage.objects.create(
                        portfolio=portfolio,
                        image=image,
                        order=i
                    )
            
            # 共同制作者の処理
            coauthors_data = request.POST.get('coauthors_data', '[]')
            try:
                coauthors = json.loads(coauthors_data)
                
                for coauthor in coauthors:
                    if coauthor.get('type') == 'internal':
                        user_id = coauthor.get('user_id', '').strip()
                        if user_id:
                            try:
                                from django.contrib.auth import get_user_model
                                User = get_user_model()
                                user = User.objects.get(id=user_id)
                                CoAuthor.objects.create(portfolio=portfolio, user=user)
                            except (User.DoesNotExist, ValueError):
                                pass
                    elif coauthor.get('type') == 'external':
                        name = coauthor.get('name', '').strip()
                        url = coauthor.get('url', '').strip()
                        if name:
                            CoAuthor.objects.create(
                                portfolio=portfolio,
                                ex_account=f"{name}|{url}" if url else name
                            )
            except json.JSONDecodeError:
                pass
            
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
    """ログアウト（GETでもPOSTでも対応）"""
    logout(request)
    return redirect('home')


def user_search_api(request):
    """ユーザー検索API（Select2用）"""
    from django.http import JsonResponse
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    term = request.GET.get('term', '')
    
    if term:
        users = User.objects.filter(username__icontains=term)[:10]
    else:
        users = User.objects.all()[:10]
    
    results = []
    for user in users:
        results.append({
            'id': str(user.id),
            'text': user.username,
            'profile_image': user.profile_image.url if user.profile_image else '/static/Portfolio/img/default_user.png'
        })
    
    return JsonResponse({'results': results})