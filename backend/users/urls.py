# from django.contrib import admin
from django.urls import path
from .views import RegisterView, LoginView, list_users, user_info_change, ChangePassword

app_name = "users"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("", list_users, name="list"),
    path("<int:pk>/", user_info_change, name="delete"),
    path("<int:pk>/change-password/", ChangePassword.as_view(), name="change_password"),
    path("<int:pk>/info-change/", user_info_change, name="info_change"),
    # path("/<int:pk>/", list_users, name="list"),
]
