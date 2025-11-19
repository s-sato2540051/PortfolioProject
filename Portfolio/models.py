from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from taggit.managers import TaggableManager

from django.contrib.auth import get_user_model
User = get_user_model()

'''
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
'''

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolios")
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="portfolio_thumbnails/")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager() 
    external_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

class PortfolioImage(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="portfolio_images/")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

class CoAuthor(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="coauthors")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="coauthored_portfolios")
    ex_account = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        if self.user:
            return self.user.username
        return self.ex_account or "Unknown"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "portfolio")
