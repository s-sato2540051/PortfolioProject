from django.contrib import admin
from .models import User, Portfolio, PortfolioImage,  CoAuthor, Like
from taggit.models import Tag

# タグ管理
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

# ポートフォリオの追加画像（インライン）
class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 4
    max_num = 4

# 共同制作者（インライン）
class CoAuthorInline(admin.TabularInline):
    model = CoAuthor
    extra = 1
    max_num = 5

# ポートフォリオ管理
@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_public", "created_at")
    list_filter = ("is_public", "created_at")
    search_fields = ("title", "description", "user__username")

    inlines = [PortfolioImageInline, CoAuthorInline]

    fieldsets = (
        (None, {
            "fields": ("user", "title", "description", "thumbnail", "is_public")
        }),
        ("タグ・共同制作者", {
            "fields": ("tags",),
            "description": "タグを選択。共同制作者は下のインラインで追加"
        }),
        ("外部リンク（任意）", {
            "fields": ("external_link",),
            "classes": ("collapse",)
        }),
    )


