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


# Utiliza APIView para reutilização de código... Herança
class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = CustomUser.objects.filter()
        serializer = RegisterSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # permissao = Permissoes.objects.filter(permissao="ADMINISTRADOR")
        # if request.user.permissao != permissao.id_permissao:

        if not request.user.is_superuser:
            return Response(
                {"detail": "Apenas administradores podem criar usuários."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.error_messages, status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(
            {"message": "Usuário criado com sucesso."}, status.HTTP_201_CREATED
        )


class LoginView(APIView):
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
                {"detail": "Credenciais inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "Usuário desativado."}, status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user=user)
        return Response(
            {
                "refresh": str(refresh),
                "token": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


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
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
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


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        # Mudar para id_usuario, quando mudar o id

        user = CustomUser.objects.filter(pk=pk)
        if not user:
            return Response(
                {"detail": "Usuário não cadastrado."}, status=status.HTTP_404_NOT_FOUND
            )

        if pk != request.user.id:
            return Response(
                {"detail": "Não é possível alterar dados de outro usuário."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        new_password_confirm = request.data.get("new_password_confirm")

        if not old_password or not new_password or not new_password_confirm:
            return Response(
                {"detail": "Por favor insira todos os campos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != new_password_confirm:
            return Response(
                {"detail": "As senhas não correspondem"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = request.user.username

        user_authenticated = authenticate(username=username, password=old_password)
        if user_authenticated is None:
            return Response(
                {"detail": "Senha atual incorreta."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user_authenticated.set_password(new_password)
        user_authenticated.save()

        return Response(
            {"detail": "Senha atualizada com sucesso."}, status=status.HTTP_200_OK
        )


def _find_user_by_Id(id):
    try:
        user = CustomUser.objects.get(pk=id)
    except CustomUser.DoesNotExist:
        return Response(
            {"detail": f"Usuário {id} não encontrado."},
            status.HTTP_404_NOT_FOUND,
        )
    return user


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = _find_user_by_Id(pk)
        serializer = RegisterSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        user = _find_user_by_Id(pk)

        if user.username != request.user.username and not request.user.is_superuser:
            return Response(
                {"detail": "Não é possível alterar dados de outro usuário."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if request.data.get("password"):
            return Response(
                {"detail": "Não é possível alterar a senha do usuário por aqui."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
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
            return Response(
                {"detail": "Usuário atualizado com sucesso."}, status.HTTP_200_OK
            )

    def delete(self, request, pk):
        user = _find_user_by_Id(pk)
        user.is_active = False
        user.save()
        return Response(
            {"detail": "Usuário desativado com sucesso."}, status.HTTP_200_OK
        )
