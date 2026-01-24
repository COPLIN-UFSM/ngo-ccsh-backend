# from django.contrib import admin
from django.urls import path
from .views import LoginView, RegisterView, ForgotPasswordView, ListUsers

app_name = "users"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("all/", ListUsers.as_view(), name="all"),
]
