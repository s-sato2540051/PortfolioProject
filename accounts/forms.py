from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "bio", "profile_image", "external_link")

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("username", "email", "bio", "profile_image", "external_link")
        
class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        label="メールアドレス",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレス'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'bio', 'profile_image', 'external_link')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '自己紹介', 'rows': 3}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'external_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
        }
        labels = {
            'username': 'ユーザー名',
            'bio': '自己紹介',
            'profile_image': 'プロフィール画像',
            'external_link': '外部リンク',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'パスワード'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'パスワード（確認）'
        })
        self.fields['password1'].label = 'パスワード'
        self.fields['password2'].label = 'パスワード（確認）'
        

from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'ユーザー名'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control','placeholder': 'パスワード'})
    )


class ProfileEditForm(forms.ModelForm):
    """プロフィール編集用フォーム"""
    class Meta:
        model = User
        fields = ('username', 'email', 'bio', 'profile_image', 'external_link')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレス'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '自己紹介', 'rows': 4}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'external_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
        }
        labels = {
            'username': 'ユーザー名',
            'email': 'メールアドレス',
            'bio': '自己紹介',
            'profile_image': 'プロフィール画像',
            'external_link': '外部リンク',
        }
        
class ContactForm(forms.Form):
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
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'お問い合わせ内容をご記入ください'})
    )