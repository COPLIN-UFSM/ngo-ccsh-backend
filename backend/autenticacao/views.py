from datetime import datetime

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from autenticacao.services import trigger_password_reset_flow
from usuarios.models import Usuario


class RecoverPasswordView(APIView):
    """Recover password with email"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Recupera senha",
        description="Inicia o fluxo de recuperação de senha via email.",
        responses={
            200: OpenApiResponse(description="Link de recuperação enviado ao email"),
            400: OpenApiResponse(description="Email não informado"),
            404: OpenApiResponse(description="Email não encontrado"),
        },
        tags=["autenticacao"],
    )
    def post(self, request):
        email = request.data.get("email", None)
        if not email:
            return Response(
                {"detail": "Por favor, forneça o email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = Usuario.objects.filter(email=email).first()
        if not user:
            return Response({"detail": "Email não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        trigger_password_reset_flow(user=user)

        return Response(
            {"detail": "Link de recuperação enviado ao seu email."},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Login",
        description="Autentica o usuário e retorna os tokens JWT de acesso e atualização.",
        responses={
            200: OpenApiResponse(description="Login realizado com sucesso"),
            400: OpenApiResponse(description="Usuário e senha são obrigatórios"),
            401: OpenApiResponse(description="Credenciais inválidas"),
        },
        tags=["autenticacao"],
    )
    def post(self, request):
        username = request.data.get("matricula")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "Dados não inseridos. Por favor insira o usuário e a senha."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {
                    "detail": "Credenciais inválidas.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.last_login = datetime.now()
        user.save()

        refresh = RefreshToken.for_user(user=user)
        refresh["is_superuser"] = user.is_superuser
        refresh["matricula"] = user.get_username()

        return Response(
            {
                "refresh": str(refresh),
                "token": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )
