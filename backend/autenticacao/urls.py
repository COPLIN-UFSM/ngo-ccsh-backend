from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from autenticacao.views import (
    LoginView,
    RecoverPasswordView,
)

app_name = "autenticacao"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("recuperar-senha/", RecoverPasswordView.as_view(), name="recuperar_senha"),
]
