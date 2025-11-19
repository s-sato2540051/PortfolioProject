from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),  
    path("mypage/", views.my_page, name="my_page"),  
    path("portfolio/<int:pk>/", views.portfolio_detail, name="portfolio_detail"),
    path("portfolio/create/", views.portfolio_create, name="portfolio_create"),
]