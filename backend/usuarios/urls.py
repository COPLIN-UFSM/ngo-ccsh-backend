from django.urls import path

from usuarios.views import UserListView, UserDetailsView, ChangePasswordView

app_name = "usuarios"

urlpatterns = [
    path("", UserListView.as_view(), name="userView"),
    path("<int:id_usuario>/", UserDetailsView.as_view(), name="single_info"),
    path("<int:id_usuario>/senha/", ChangePasswordView.as_view(), name="change_password")
]
