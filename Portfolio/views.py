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
    
    # 共同制作者の外部アカウントを整形
    coauthors_processed = []
    # **注意**: ここでのアイコン・色判定は以前のロジックに基づいており、views.py側でブランドカラー（bg_color）を定義していないため、ここでは便宜的にicon_colorを使用します。
    # 共同制作者の表示はテンプレート側で行うため、このビューのロジックは既存のまま維持します。
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
                bg_color = '#6c757d' # デフォルト
                
                if 'twitter.com' in url or 'x.com' in url:
                    icon = 'bi-twitter-x'
                    bg_color = '#000000' # X Black
                elif 'youtube.com' in url or 'youtu.be' in url:
                    icon = 'bi-youtube'
                    bg_color = '#FF0000' # YouTube Red
                elif 'github.com' in url:
                    icon = 'bi-github'
                    bg_color = '#333333' # GitHub Dark
                
                coauthors_processed.append({
                    'type': 'external',
                    'name': name,
                    'url': url,
                    'icon': icon,
                    'bg_color': bg_color # bg_colorを使用
                })
            else:
                coauthors_processed.append({
                    'type': 'external_simple',
                    'name': coauthor.ex_account
                })
    
    return render(request, "portfolio_detail.html", {
            "portfolio": p,
            # "coauthors_processed": coauthors_processed, # 既存のコンテキストがあれば残す
            "is_liked": is_liked # ★これをコンテキストに追加★
        })


@login_required # ログインしていないと実行できない
@require_POST # POSTメソッドのみ許可
def like_toggle(request, pk):
    """
    作品のいいねを切り替える (トグル) API
    """
    try:
        # UUIDをpkとして受け取っていると仮定
        portfolio = Portfolio.objects.get(pk=pk)
    except Portfolio.DoesNotExist:
        # 作品が存在しない場合は404エラーを返す
        raise Http404("作品が見つかりません。")

    user = request.user
    
    # 既にいいね済みか確認
    # p.likes.filter(user=request.user) は p.liked_by.filter(user=request.user) とほぼ同等
    is_liked = Like.objects.filter(user=user, portfolio=portfolio).exists()
    
    if is_liked:
        # いいねを解除 (削除)
        Like.objects.filter(user=user, portfolio=portfolio).delete()
        new_status = False
    else:
        # いいねを登録 (作成)
        try:
            # Like.objects.create(user=user, portfolio=portfolio)
            # IntegrityErrorを防ぐためget_or_createを使うか、
            # your_model.pyのunique_together設定に頼る
            Like.objects.create(user=user, portfolio=portfolio)
            new_status = True
        except IntegrityError:
            # 稀に発生する重複登録エラーを防ぐための念のため
            new_status = False # 作成失敗

    # いいねの総数を取得
    # あなたのモデル設計(related_name='likes')に合わせ p.likes.count() を使用
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
                # テンプレート側の処理により、tags_dataはカンマ区切りの文字列を想定
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
                        # テンプレートから渡されるのはユーザーID
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
    
    # 投稿フォームの表示時に使用頻度順にタグを取得 (Ajaxではなく、人気のタグボタン用)
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
        # 何も入力がない場合は最近のユーザーなどを返す（ここでは簡略化のため空リストまたは少数を返す）
        users = [] 
    
    results = []
    for user in users:
        # 注意: ユーザーモデルに profile_image があることを前提としています
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
        # 入力された文字列を含むタグを検索
        tags = Tag.objects.filter(name__icontains=term).order_by('name')[:50]
    else:
        # 何も入力がない場合は、人気のタグを返す
        tags = Tag.objects.annotate(
            usage_count=Count('taggit_taggeditem_items')
        ).filter(usage_count__gt=0).order_by('-usage_count', 'name')[:20]

    results = []
    for tag in tags:
        results.append({
            'id': tag.name,  # IDもテキストもタグ名にする
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
            
            # タグの更新（既存のタグを削除してから追加）
            portfolio.tags.clear()
            tags_data = form.cleaned_data.get('tags', '')
            if tags_data:
                tags_data = tags_data.replace("'", "").replace('"', '').replace('[', '').replace(']', '')
                tag_list = [tag.strip() for tag in tags_data.split(',') if tag.strip()]
                for tag in tag_list:
                    portfolio.tags.add(tag)
            
            # 追加画像の更新（既存の画像を削除してから追加）
            portfolio.images.all().delete()
            for i in range(1, 5):
                image = form.cleaned_data.get(f'image{i}')
                if image:
                    PortfolioImage.objects.create(
                        portfolio=portfolio,
                        image=image,
                        order=i
                    )
            
            # 共同制作者の更新（既存の共同制作者を削除してから追加）
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
    
    # 投稿フォームの表示時に使用頻度順にタグを取得
    popular_tags = Tag.objects.annotate(
        usage_count=Count('taggit_taggeditem_items')
    ).filter(usage_count__gt=0).order_by('-usage_count', 'name')[:50]
    
    # 既存の共同制作者情報を取得
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
    
    # 既存の追加画像を取得
    existing_images = list(portfolio.images.all().order_by('order'))
    
    return render(request, "portfolio_create.html", {  # portfolio_create.htmlを使用
        "form": form,
        "portfolio": portfolio,  # 編集モードであることを示すため
        "popular_tags": popular_tags,
        "existing_coauthors": json.dumps(existing_coauthors),
        "existing_images": existing_images,
    })