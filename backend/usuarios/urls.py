from django.urls import path

from usuarios.views import UserListView, UserDetailsView, ChangePasswordView

app_name = "usuarios"

urlpatterns = [
    path("", UserListView.as_view(), name="user_list"),
    path("<int:id>/", UserDetailsView.as_view(), name="user_details"),
    path("<int:id>/senha/", ChangePasswordView.as_view(), name="change_password")
]
