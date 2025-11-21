from django import forms
from .models import Portfolio
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
        if self.instance.pk:
            self.initial['tags'] = ','.join([tag.name for tag in self.instance.tags.all()])