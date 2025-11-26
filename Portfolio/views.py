from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db.models import Count, Q 
from django.http import JsonResponse 
import json

from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST 
from django.http import JsonResponse, Http404
from django.db import IntegrityError 

from .models import Portfolio, PortfolioImage, CoAuthor ,Like 
from .forms import PortfolioForm
from taggit.models import Tag


def home(request):
    portfolios = Portfolio.objects.filter(is_public=True).order_by("-created_at")[:10]
    return render(request, "home.html", {"portfolios": portfolios})


@login_required
def my_page(request):
    user = request.user
    #自分が作者、共同制作者の作品を取得
    portfolios = Portfolio.objects.filter(
        Q(user=user) | Q(coauthors__user=user) 
    ).distinct().order_by("-created_at") #重複禁止

    return render(request, "my_page.html", {"portfolios": portfolios})


def user_page(request, username):
    """他のユーザーのページを表示"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = get_object_or_404(User, username=username)
    
    #自分のページならmypageに
    if request.user.is_authenticated and request.user.username == username:
        return redirect('my_page')
    
    # 公開作品のみ表示 (相手が作者または共同制作者の作品)
    portfolios = Portfolio.objects.filter(
        Q(user=user) | Q(coauthors__user=user), 
        is_public=True
    ).distinct().order_by("-created_at")
    
    return render(request, "user_page.html", {
        "page_user": user,
        "portfolios": portfolios
    })


def portfolio_detail(request, pk):
    p = get_object_or_404(Portfolio, pk=pk)
    
    is_liked = False
    if request.user.is_authenticated:
        is_liked = p.likes.filter(user=request.user).exists()
    
    # 共同制作者の外部アカウントをそれっぽくする
    coauthors_processed = []
    for coauthor in p.coauthors.all():
        if coauthor.user:
            coauthors_processed.append({
                'type': 'internal',
                'user': coauthor.user
            })
        else:
            if '|' in coauthor.ex_account:
                name, url = coauthor.ex_account.split('|', 1)
                
                # URLからアイコンを判定
                icon = 'bi-link-45deg'
                bg_color = '#6c757d' # デフォ
                
                if 'twitter.com' in url or 'x.com' in url:
                    icon = 'bi-twitter-x'
                    bg_color = '#000000' 
                elif 'youtube.com' in url or 'youtu.be' in url:
                    icon = 'bi-youtube'
                    bg_color = '#FF0000' 
                elif 'github.com' in url:
                    icon = 'bi-github'
                    bg_color = '#333333'
                
                coauthors_processed.append({
                    'type': 'external',
                    'name': name,
                    'url': url,
                    'icon': icon,
                    'bg_color': bg_color 
                    
                })
            else:
                coauthors_processed.append({
                    'type': 'external_simple',
                    'name': coauthor.ex_account
                })
    
    return render(request, "portfolio_detail.html", {
            "portfolio": p,
            "is_liked": is_liked 
        })


@login_required
@require_POST 
def like_toggle(request, pk):
    """
    作品のいいねを切り替える (トグル) API
    """
    try:
        portfolio = Portfolio.objects.get(pk=pk)
    except Portfolio.DoesNotExist:
        raise Http404("作品が見つかりません。")

    user = request.user
    
    # 既にいいね済みか確認
    is_liked = Like.objects.filter(user=user, portfolio=portfolio).exists()
    
    if is_liked:
        Like.objects.filter(user=user, portfolio=portfolio).delete()
        new_status = False
    else:
        try:
            Like.objects.create(user=user, portfolio=portfolio)
            new_status = True
        except IntegrityError:
            new_status = False 

    # いいねの総数を取得
    like_count = portfolio.likes.count() 

    return JsonResponse({
        'status': 'ok',
        'is_liked': new_status,
        'like_count': like_count,
        'message': 'いいねしました' if new_status else 'いいねを解除しました'
    })

@login_required
def portfolio_create(request):
    if request.method == "POST":
        form = PortfolioForm(request.POST, request.FILES)
        if form.is_valid():
            portfolio = form.save(commit=False)
            portfolio.user = request.user
            portfolio.save() 
            
            # タグの処理
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
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    term = request.GET.get('term', '')
    
    if term:
        # 自分以外のユーザーを検索
        users = User.objects.filter(username__icontains=term).exclude(id=request.user.id if request.user.is_authenticated else None)[:10]
    else:
        users = [] 
    
    results = []
    for user in users:
        profile_image_url = user.profile_image.url if hasattr(user, 'profile_image') and user.profile_image else '/static/Portfolio/img/default_user.png'
        
        results.append({
            'id': str(user.id),
            'text': user.username,
            'profile_image': profile_image_url
        })
    
    return JsonResponse({'results': results})


def tag_search_api(request):
    """タグ検索API（Select2用） - 新規追加"""
    term = request.GET.get('term', '')
    
    if term:
        tags = Tag.objects.filter(name__icontains=term).order_by('name')[:50]
    else:
        tags = Tag.objects.annotate(
            usage_count=Count('taggit_taggeditem_items')
        ).filter(usage_count__gt=0).order_by('-usage_count', 'name')[:20]

    results = []
    for tag in tags:
        results.append({
            'id': tag.name, 
            'text': tag.name,
        })
    
    return JsonResponse({'results': results})


@login_required
def portfolio_edit(request, pk):
    """ポートフォリオの編集"""
    portfolio = get_object_or_404(Portfolio, pk=pk)
    
    # 作者または共同制作者でない場合は403エラー
    is_coauthor = portfolio.coauthors.filter(user=request.user).exists()
    if portfolio.user != request.user and not is_coauthor:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("この作品を編集する権限がありません。")
    
    if request.method == "POST":
        form = PortfolioForm(request.POST, request.FILES, instance=portfolio)
        if form.is_valid():
            portfolio = form.save(commit=False)
            portfolio.save()
            
            portfolio.tags.clear()
            tags_data = form.cleaned_data.get('tags', '')
            if tags_data:
                tags_data = tags_data.replace("'", "").replace('"', '').replace('[', '').replace(']', '')
                tag_list = [tag.strip() for tag in tags_data.split(',') if tag.strip()]
                for tag in tag_list:
                    portfolio.tags.add(tag)
            
            portfolio.images.all().delete()
            for i in range(1, 5):
                image = form.cleaned_data.get(f'image{i}')
                if image:
                    PortfolioImage.objects.create(
                        portfolio=portfolio,
                        image=image,
                        order=i
                    )
            
            portfolio.coauthors.all().delete()
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
            
            return redirect("portfolio_detail", pk=portfolio.pk)
    else:
        form = PortfolioForm(instance=portfolio)
    
    popular_tags = Tag.objects.annotate(
        usage_count=Count('taggit_taggeditem_items')
    ).filter(usage_count__gt=0).order_by('-usage_count', 'name')[:50]
    
    existing_coauthors = []
    for coauthor in portfolio.coauthors.all():
        if coauthor.user:
            existing_coauthors.append({
                'type': 'internal',
                'user_id': str(coauthor.user.id),
                'username': coauthor.user.username,
                'profile_image': coauthor.user.profile_image.url if coauthor.user.profile_image else '/static/Portfolio/img/default_user.png'
            })
        else:
            if '|' in coauthor.ex_account:
                name, url = coauthor.ex_account.split('|', 1)
                existing_coauthors.append({
                    'type': 'external',
                    'name': name,
                    'url': url
                })
            else:
                existing_coauthors.append({
                    'type': 'external',
                    'name': coauthor.ex_account,
                    'url': ''
                })
    
    existing_images = list(portfolio.images.all().order_by('order'))
    
    return render(request, "portfolio_create.html", { 
        "form": form,
        "portfolio": portfolio,  
        "popular_tags": popular_tags,
        "existing_coauthors": json.dumps(existing_coauthors),
        "existing_images": existing_images,
    })
    

