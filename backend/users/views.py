# Create your views here.
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .serializers import RegisterSerializer, UserSerializer

# Autenticacao + JWT
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

# from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import CustomUser

# # Token acesso único -> Para criar mudança de senha quando se esqueceu a senha!!!
# from django.contrib.auth.tokens import (
#     default_token_generator,
# )  # Token de acesso único, pesquisa sobre;;
# from django.utils.http import urlsafe_base64_encode
# from django.utils.encoding import force_bytes
# from django.contrib.auth import get_user_model


class LoginView(APIView):
    """Login user"""

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {
                    "detail": "Dados não inseridos. Por favor insira o usuário e a senha."
                },
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

        refresh = RefreshToken.for_user(user=user)
        return Response(
            {
                "refresh": str(refresh),
                "token": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


class UserView(APIView):
    """Get all users and Register user"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = CustomUser.objects.filter(is_active=True)
        serializer = RegisterSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response(
                {"detail": "Apenas administradores podem criar usuários."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(
            {"message": "Usuário criado com sucesso."}, status.HTTP_201_CREATED
        )


class ChangePasswordView(APIView):
    """Change password with user autenticated and current password"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        user = CustomUser.objects.filter(pk=pk).first()

        if user is None:
            return Response(
                {"detail": "Usuário não cadastrado."}, status=status.HTTP_404_NOT_FOUND
            )

        if pk != request.user.id and not request.user.is_superuser:
            return Response(
                {"detail": "Não é possível alterar dados de outro usuário."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        new_password_confirm = request.data.get("new_password_confirm")

        if not new_password or not new_password_confirm:
            return Response(
                {"detail": "Por favor insira todos os campos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != new_password_confirm:
            return Response(
                {"new_password": "Os dados da nova senha não correspondem."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = request.user.username

        if not request.user.is_superuser:
            if not old_password:
                return Response(
                    {"old_password": "Por favor insira a senha atual."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_authenticated = authenticate(username=username, password=old_password)
            if user_authenticated is None:
                return Response(
                    {"old_password": "Senha atual incorreta."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        user.set_password(new_password)
        user.save()
        return Response(
            {"detail": "Senha atualizada com sucesso."}, status=status.HTTP_200_OK
        )


def _find_user_by_Id(id):
    """Return user or None"""
    try:
        user = CustomUser.objects.get(pk=id)
    except CustomUser.DoesNotExist:
        return None
    return user


class UserInfoView(APIView):
    """GET/PATCH/DELETE -> especific user"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = _find_user_by_Id(pk)
        if user is None:
            return Response(
                {"detail": f"Usuário {id} não encontrado."},
                status.HTTP_404_NOT_FOUND,
            )
        serializer = RegisterSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        user = _find_user_by_Id(pk)
        if user is None:
            return Response(
                {"detail": f"Usuário {id} não encontrado."},
                status.HTTP_404_NOT_FOUND,
            )

        if user.id != request.user.pk and not request.user.is_superuser:
            return Response(
                {"detail": "Não é possível alterar dados de outro usuário."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = UserSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        changes = {}
        for field, value in serializer.validated_data.items():
            if getattr(user, field) != value:
                changes[field] = value

        if not changes:
            return Response(
                {"detail": f"Nenhuma mudança realizada."},
                status.HTTP_200_OK,
            )

        serializer.save()
        changes.__str__()
        return Response(
            {"detail": "Campos  atualizado com sucesso.", "changes": changes},
            status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        user = _find_user_by_Id(pk)
        if user is None:
            return Response(
                {"detail": f"Usuário com id: '{pk}' não encontrado."},
                status.HTTP_404_NOT_FOUND,
            )
        if user.id != request.user.pk and not request.user.is_superuser:
            return Response(
                {"detail": "Não é possível deletar outro usuário."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.is_active = False
        user.save()
        return Response(status.HTTP_204_NO_CONTENT)


from django.core.mail import send_mail
import os


# Continuar daqui....
def send_email(user):
    refresh = RefreshToken.for_user(user=user)
    token_access = str(refresh.access_token)
    # send_mail(
    #     "Portal Transparência CCSH - Recuperação de Senha.",
    #     f"Olá {user.username}, Se você solicitou a alteração de senha. Utilize este link para altera-lá: {token_access}",
    #     os.getenv("EMAIL_HOST_USER"),
    #     [user.email],
    #     fail_silently=False,
    # )


class RecoverPasswordView(APIView):
    """Recover password with email"""

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        if not username:
            return Response(
                {"detail": "Por favor, forneça o nome de usuário."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = CustomUser.objects.filter(username=username)
        if not user:
            return Response(
                {"detail": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        # send_email(user)
        return Response(
            {"detail": "Token de acesso enviado ao email do usuário."},
            status=status.HTTP_200_OK,
        )
