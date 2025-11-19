from django import forms
from django_select2.forms import ModelSelect2TagWidget
from .models import Portfolio
from taggit.models import Tag
from django.db.models import Count

class TagWidget(ModelSelect2TagWidget):
    model = Tag
    search_fields = [
        'name__icontains',
    ]


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ["title", "description", "thumbnail", "is_public", "tags", "external_link"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "thumbnail": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "external_link": forms.URLInput(attrs={"class": "form-control"}),

            "tags": TagWidget(
                attrs={"data-placeholder": "タグを入力", "class": "form-control"},
                dependent_fields={},
                max_results=50,
            ),
        }
    def clean_tags(self):
        tags = self.cleaned_data.get("tags")
        if not tags:
            return []
        clean_tags = []
        for t in tags:
            # 余計な文字を除去
            t = str(t).replace("[","").replace("]","").replace("'","").strip()
            if t:
                clean_tags.append(t)
        return clean_tags    
    
