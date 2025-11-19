from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from .forms import SignUpForm, LoginForm

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("my_page")  
    else:
        form = SignUpForm()
    return render(request, "sign_up.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST) 
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user) 
            return redirect("my_page")
    else:
        form = LoginForm(request) 

    return render(request, "login.html", {"form": form})

from django.contrib.auth import logout
def logout_view(request):
    logout(request)
    return redirect('home')