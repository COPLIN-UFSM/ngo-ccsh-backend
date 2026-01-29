# from django.contrib import admin
from django.urls import path
from .views import RegisterView, ListUsers, LoginView, PerfilView
from .views import list_users, user_details
from rest_framework_simplejwt.views import TokenObtainPairView

app_name = "users"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("perfil/", PerfilView.as_view(), name="perfil"),
    # path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("all/", TokenObtainPairView.as_view(), name="all"),
    path("all/", ListUsers.as_view(), name="all"),
    path("list-users/", list_users, name="list_users"),
    path("details/<int:pk>", user_details, name="list_users"),
]
