# from django.contrib import admin
from django.urls import path
from .views import (
    UserView,
    LoginView,
    UserInfoView,
    ChangePasswordView,
    RecoverPasswordView,
    UserView,
)

app_name = "users"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("", UserView.as_view(), name="user"),
    path("<int:pk>/", UserInfoView.as_view(), name="user_info"),
    path(
        "<int:pk>/change-password/",
        ChangePasswordView.as_view(),
        name="change_password",
    ),
    path("recover-password/", RecoverPasswordView.as_view(), name="recover_password"),
]
