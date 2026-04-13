# from django.contrib import admin
from django.urls import path
from users.views import (
    UserView,
    LoginView,
    UserInfoView,
    ChangePasswordView,
    RecoverPasswordView,
    UpdatePermissionUser,
    UserView,
)

app_name = "users"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path(
        "permission-update/<int:pk>/",
        UpdatePermissionUser.as_view(),
        name="permission_update"
    ),
    path("recover-password/", RecoverPasswordView.as_view(), name="recover_password"),
    path("", UserView.as_view(), name="userView"),
    
    path("<int:pk>/", UserInfoView.as_view(), name="single_info"),
    path(
        "change-password/<int:pk>/",
        ChangePasswordView.as_view(),
        name="change_password",
    ),
]
