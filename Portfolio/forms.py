from django import forms
from .models import Portfolio, PortfolioImage, CoAuthor
from taggit.models import Tag
from django.db.models import Count

class PortfolioForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control",
            "id": "tag-input",
            "style": "display:none;"
        })
    )
    
    image1 = forms.ImageField(required=False, label="追加画像1")
    image2 = forms.ImageField(required=False, label="追加画像2")
    image3 = forms.ImageField(required=False, label="追加画像3")
    image4 = forms.ImageField(required=False, label="追加画像4")
    
    class Meta:
        model = Portfolio
        fields = ["title", "description", "thumbnail", "is_public", "external_link"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "thumbnail": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "external_link": forms.URLInput(attrs={"class": "form-control"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 既存のタグを初期値として設定
        if self.instance.pk:
            self.initial['tags'] = ','.join([tag.name for tag in self.instance.tags.all()])
            
class UserContactForm(forms.Form):
    name = forms.CharField(
        label='お名前',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'お名前'})
    )
    
    email = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    
    message = forms.CharField(
        label='お問い合わせ内容',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'お問い合わせ内容をご入力ください'})
    )