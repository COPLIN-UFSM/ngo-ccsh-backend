# from django.contrib import admin
from django.urls import path
from .views import RegisterView, ListUsers, LoginView, PerfilView

app_name = "users"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path('perfil/', PerfilView.as_view(), name='perfil'),
    # path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("all/", ListUsers.as_view(), name="all"),
]
