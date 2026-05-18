# Create your views here.
from datetime import datetime

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, UserSerializer

# Autenticação + JWT
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from usuarios.models import Usuario
from usuarios.services import trigger_password_reset_flow
from usuarios.services import _find_user_by_Id


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
        tags=["usuarios"],
    )
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

        user.last_login = datetime.now()
        user.save()

        refresh = RefreshToken.for_user(user=user)
        refresh["is_superuser"] = user.is_superuser
        refresh["username"] = user.get_username()

        return Response(
            {
                "refresh": str(refresh),
                "token": str(refresh.access_token),
            },
            status=status.HTTP_200_OK
        )


class UserView(APIView):
    """View para dar listar usuários e atualizar"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Lista usuários",
        description="Retorna a lista de usuários ativos.",
        responses={
            200: OpenApiResponse(description="Lista de usuários retornada com sucesso"),
            401: OpenApiResponse(description="Usuário não autenticado"),
        },
        tags=["usuarios"],
    )
    def get(self, request):
        """
        Retorna um usuário por ID
        """
        users = Usuario.objects.filter(is_active=True).order_by("id")
        serializer = RegisterSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cria usuário",
        description="Cria um novo usuário (apenas administradores).",
        responses={
            201: OpenApiResponse(description="Usuário criado com sucesso"),
            400: OpenApiResponse(description="Dados inválidos para criação do usuário"),
            403: OpenApiResponse(description="Apenas administradores podem criar usuários"),
        },
        tags=["usuarios"],
    )
    def post(self, request):
        """
        Cria ou atualiza um usuário por ID
        """
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
            {"detail": "Usuário criado com sucesso."}, status.HTTP_201_CREATED
        )


class UpdatePermissionUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Atualiza permissões do usuário",
        description="Atualiza permissões de superusuário e/ou staff de um usuário por ID.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=int,
                location="path",
                description="ID do usuário a ter as permissões alteradas",
                required=True,
            )
        ],
        responses={
            200: OpenApiResponse(description="Permissões atualizadas com sucesso"),
            400: OpenApiResponse(description="Nenhuma permissão nova informada"),
            401: OpenApiResponse(description="Apenas administradores podem alterar permissões"),
            404: OpenApiResponse(description="Usuário não encontrado"),
        },
        tags=["usuarios"],
    )
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
                {"detail": f"Usuário com id: {pk}, não encontrado."},
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


class ChangePasswordView(APIView):
    """Change password with user authenticated and current password"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Altera senha",
        description="Altera a senha de um usuário autenticado por ID.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=int,
                location="path",
                description="ID do usuário",
                required=True,
            )
        ],
        responses={
            200: OpenApiResponse(description="Senha atualizada com sucesso"),
            400: OpenApiResponse(description="Dados inválidos para alteração de senha"),
            401: OpenApiResponse(description="Senha atual incorreta"),
            403: OpenApiResponse(description="Não é possível alterar senha de outro usuário"),
            404: OpenApiResponse(description="Usuário não cadastrado"),
        },
        tags=["usuarios"],
    )
    def patch(self, request, pk):
        user = Usuario.objects.filter(pk=pk).first()

        if user is None:
            return Response(
                {"detail": "Usuário não cadastrado."}, status=status.HTTP_404_NOT_FOUND
            )

        if pk != request.user.id and not request.user.is_superuser:
            return Response(
                {"detail": "Não é possível alterar dados de outro usuário."},
                status=status.HTTP_403_FORBIDDEN,
            )

        old_password = request.data.get("old_password")
        new_password = request.data.get("password1")
        new_password_confirm = request.data.get("password2")

        if not new_password or not new_password_confirm:
            return Response(
                {"detail": "Por favor insira todos os campos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != new_password_confirm:
            return Response(
                {"detail": "Os dados da nova senha não correspondem."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = request.auth
        # Se for admin alterando a senha de outro, ou se o token permitir, pula a senha antiga
        is_admin_changing_other = (
            request.user.is_superuser and pk != request.user.id
        )
        can_skip_old_password = (
            (token and token.get("allow_password_change", False))
            or is_admin_changing_other
        )

        if not can_skip_old_password:
            if not old_password:
                return Response(
                    {"detail": "Por favor insira a senha atual."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            username = user.username
            user_authenticated = authenticate(username=username, password=old_password)
            if user_authenticated is None:
                return Response(
                    {"detail": "Senha atual incorreta."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        user.set_password(new_password)
        user.save()
        return Response(
            {"detail": "Senha atualizada com sucesso."}, status=status.HTTP_200_OK
        )


class UserInfoView(APIView):
    """Retorna informações sobre um usuário em específico, dado seu ID"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Busca usuário",
        description="Retorna os dados de um usuário pelo ID.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=int,
                location="path",
                description="ID do usuário",
                required=True,
            )
        ],
        responses={
            200: OpenApiResponse(description="Dados do usuário retornados com sucesso"),
            404: OpenApiResponse(description="Usuário não encontrado"),
        },
        tags=["usuarios"],
    )
    def get(self, request, pk):
        """
        Mostra dados de um usuário
        """
        user = _find_user_by_Id(pk)
        if user is None:
            return Response(
                {"detail": f"Usuário {id} não encontrado."},
                status.HTTP_404_NOT_FOUND,
            )
        serializer = RegisterSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Atualiza usuário",
        description="Atualiza parcialmente os dados de um usuário pelo ID.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=int,
                location="path",
                description="ID do usuário",
                required=True,
            )
        ],
        responses={
            200: OpenApiResponse(description="Dados do usuário atualizados com sucesso"),
            400: OpenApiResponse(description="Dados inválidos para atualização"),
            403: OpenApiResponse(description="Não é possível alterar dados de outro usuário"),
            404: OpenApiResponse(description="Usuário não encontrado"),
        },
        tags=["usuarios"],
    )
    def patch(self, request, pk):
        """
        Atualiza os dados de um usuário
        """
        user = _find_user_by_Id(pk)
        if user is None:
            return Response(
                {"detail": f"Usuário {id} não encontrado."},
                status.HTTP_404_NOT_FOUND,
            )

        if user.id != request.user.pk and not request.user.is_superuser:
            return Response(
                {"detail": "Não é possível alterar dados de outro usuário."},
                status=status.HTTP_403_FORBIDDEN,
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

    @extend_schema(
        summary="Remove usuário",
        description="Remove (desativa) um usuário utilizando seu ID.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="path",
                description="ID do usuário a ser removido",
                required=True,
            )
        ],
        responses={
            204: OpenApiResponse(description="Usuário removido com sucesso"),
            401: OpenApiResponse(description="Não é possível deletar este usuário"),
            404: OpenApiResponse(description="Usuário não encontrado"),
        },
        tags=["usuarios"],
    )
    def delete(self, request, id):
        user = _find_user_by_Id(id)
        if user is None:
            return Response(
                {"detail": f"Usuário com id '{id}' não encontrado."},
                status.HTTP_404_NOT_FOUND,
            )
        if user.id != request.user.pk and not request.user.is_superuser:
            return Response(
                {"detail": "Não é possível deletar este usuário."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.is_active = False
        user.save()
        return Response(status.HTTP_204_NO_CONTENT)


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
        tags=["usuarios"],
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
            return Response(
                {"detail": "Email não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        trigger_password_reset_flow(user=user)

        return Response(
            {"detail": "Link de recuperação enviado ao seu email."},
            status=status.HTTP_200_OK,
        )
