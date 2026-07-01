from django.urls import path

from usuarios.views import UserListView, UserDetailsView, ChangePasswordView

app_name = "usuarios"

urlpatterns = [
    path("", UserListView.as_view(), name="userList"),
    path("<int:id>/", UserDetailsView.as_view(), name="userDetails"),
    path("<int:id>/senha/", ChangePasswordView.as_view(), name="changePassword")
]
