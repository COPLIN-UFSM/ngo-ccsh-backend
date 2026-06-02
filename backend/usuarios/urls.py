# from django.contrib import admin
from django.urls import path
from usuarios.views import (
    UserView,
    UserInfoView,
    ChangePasswordView,
    UpdatePermissionUserView,
)

app_name = "usuarios"

urlpatterns = [
    path("", UserView.as_view(), name="userView"),
    path("<int:pk>/", UserInfoView.as_view(), name="single_info"),
    path("trocar-senha/<int:pk>/", ChangePasswordView.as_view(), name="change_password"),
    path("atualizar-permissoes/<int:pk>/", UpdatePermissionUserView.as_view(), name="permission_update"),
]
