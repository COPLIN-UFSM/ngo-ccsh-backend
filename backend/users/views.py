# Create your views here.
from datetime import datetime
from hmac import new
import token
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
                {"detail": "Credenciais inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "Usuário desativado."}, status=status.HTTP_401_UNAUTHORIZED
            )

        user.last_login = datetime.now()
        user.save()

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
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(
            {"message": "Usuário criado com sucesso."}, status.HTTP_201_CREATED
        )


def _find_user_by_Id(id):
    """Return user or None"""
    try:
        user = CustomUser.objects.get(pk=id)
    except CustomUser.DoesNotExist:
        return None
    return user


class updatePermissionUser(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.is_superuser:
            return Response(
                {
                    "detail": "Apenas administradores podem transformar um usuário em super usuário."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = _find_user_by_Id(pk)
        if user is None:
            return Response(
                {"detail": f"Usuário com id: {pk}, não encontrado. "},
                status=status.HTTP_404_NOT_FOUND,
            )

        old_permission_super = user.is_superuser
        old_permission_staff = user.is_staff

        if request.data.get("is_superuser") is not None:
            user.is_superuser = request.data.get("is_superuser")
            user.is_staff = request.data.get("is_superuser")

        elif request.data.get("is_staff") is not None:
            user.is_staff = request.data.get("is_staff")
        else:
            return Response(
                {"detail": "Nenhuma permissão nova informada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.save()

        detail = (
            (
                "Nenhuma permissão alterada"
                if old_permission_super == user.is_superuser
                and old_permission_staff == user.is_staff
                else f"O usuário {user.username} teve seu status de usuário alterado."
            ),
        )

        return Response(
            {
                "detail": detail,
                "data": {
                    "is_superuser": user.is_superuser,
                    "is_staff": user.is_staff,
                },
            },
            status=status.HTTP_200_OK,
        )


from rest_framework_simplejwt.authentication import JWTAuthentication


class ChangePasswordView(APIView):
    """Change password with user autenticated and current password or superuser"""

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

        token = request.auth
        can_skip_old_password = token.get("allow_password_change", False)

        if not request.user.is_superuser and not can_skip_old_password:
            if not old_password:
                return Response(
                    {"old_password": "Por favor insira a senha atual."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            username = user.username
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
        return Response({"detail": "Usuário deletado com sucesso."}, status.HTTP_200_OK)


from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import AccessToken
import os


def create_token_reset(user):
    token = AccessToken.for_user(user=user)
    token["allow_password_change"] = True
    return token


from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_email_reset_password(user, token):
    link = f'token: {token}'
    
    context = {
        "username": user.username,
        "full_name": user.full_name,
        "link": link,
    }
    html_content = render_to_string("email/my_email.html", context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject="Portal Transparência CCSH - Recuperação de Senha.",
        body=text_content,
        from_email=os.getenv("EMAIL_USER"),
        to=[user.email],
        headers={"List-Unsubscribe": "<mailto:suporte@cssh.com>"},
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


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
        user = CustomUser.objects.filter(username=username).first()
        if not user:
            return Response(
                {"detail": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        token = create_token_reset(user)
        send_email_reset_password(user, token)

        return Response(
            {"detail": "Token de acesso enviado ao email do usuário."},
            status=status.HTTP_200_OK,
        )
