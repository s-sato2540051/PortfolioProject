from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"), 
    path("mypage/", views.my_page, name="my_page"), 
    path("@<str:username>/", views.user_page, name="user_page"),
    path("portfolio/<uuid:pk>/", views.portfolio_detail, name="portfolio_detail"),
    path("portfolio/create/", views.portfolio_create, name="portfolio_create"),
    path("logout/", views.logout_view, name="logout"),
    path("api/users/search/", views.user_search_api, name="user_search_api"), 
    path("api/tags/search/", views.tag_search_api, name="tag_search_api"), 
    path('portfolio/<uuid:pk>/', views.portfolio_detail, name='portfolio_detail'),
    path('portfolio/<uuid:pk>/like/', views.like_toggle, name='like_toggle'),
    path("portfolio/<uuid:pk>/edit/", views.portfolio_edit, name="portfolio_edit"),
]

