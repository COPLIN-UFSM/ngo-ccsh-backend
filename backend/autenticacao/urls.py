from django.urls import path
from autenticacao.views import (
    LoginView,
    RecoverPasswordView,
)

app_name = "autenticacao"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("recuperar-senha/", RecoverPasswordView.as_view(), name="recuperar_senha"),
]
