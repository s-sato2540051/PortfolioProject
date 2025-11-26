from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase
import uuid

from django.contrib.auth import get_user_model
User = get_user_model()


# UUID対応のTaggedItemモデル
class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class Portfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolios")
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="portfolio_thumbnails/")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(through=UUIDTaggedItem) 
    external_link = models.URLField(blank=True, null=True)
    liked_by = models.ManyToManyField(User,through='Like',related_name='liked_portfolios')

    def __str__(self):
        return self.title


class PortfolioImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="portfolio_images/")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class CoAuthor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="coauthors")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="coauthored_portfolios")
    ex_account = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        if self.user:
            return self.user.username
        return self.ex_account or "Unknown"


class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "portfolio")


class Contact(models.Model):
    """お問い合わせ・コンタクト"""
    CONTACT_TYPE_CHOICES = [
        ('support', '運営へのお問い合わせ'),
        ('portfolio', '作品作者へのコンタクト'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_contacts")
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    
    # 作品作者へのコンタクトの場合
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, null=True, blank=True, related_name="contacts")
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="received_contacts")
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_contact_type_display()} - {self.subject}"