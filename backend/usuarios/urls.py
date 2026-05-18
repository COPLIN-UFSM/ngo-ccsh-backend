# from django.contrib import admin
from django.urls import path
from usuarios.views import (
    UserView,
    LoginView,
    UserInfoView,
    ChangePasswordView,
    RecoverPasswordView,
    UpdatePermissionUserView,
    UserView,
)

app_name = "usuarios"

urlpatterns = [
    path("", UserView.as_view(), name="userView"),
    path("login/", LoginView.as_view(), name="login"),
    path("<int:pk>/", UserInfoView.as_view(), name="single_info"),
    path("recuperar-senha/", RecoverPasswordView.as_view(), name="recover_password"),
    path("trocar-senha/<int:pk>/", ChangePasswordView.as_view(), name="change_password"),
    path("atualizar-permissoes/<int:pk>/", UpdatePermissionUserView.as_view(), name="permission_update"),
]
