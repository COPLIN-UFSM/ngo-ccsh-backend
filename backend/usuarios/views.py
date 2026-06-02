# Create your views here.

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, UserSerializer

# Autenticação + JWT
from django.contrib.auth import authenticate
from usuarios.models import Usuario
from utils import response


class UserView(APIView):
    """View para dar listar usuários e atualizar"""

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
        users = Usuario.objects.filter().order_by("id")
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
            return response.not_admin_user()

        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return response.created("Usuário criado com sucesso.")


class UpdatePermissionUserView(APIView):

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
            return response.not_admin_user()


        try:
            user = Usuario.objects.get(pk=pk)
        except:
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
                {"detail": "As senhas não são iguais."},
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

    serializer_class = [UserSerializer]

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
        try:
            user = Usuario.objects.get(pk=pk)
        except:
            return Response(
                {"detail": f"Usuário com id: {pk}, não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
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
        try:
            user = Usuario.objects.get(pk=pk)
        except:
            return Response(
                {"detail": f"Usuário com id: {pk}, não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
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
                name="pk",
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
    def delete(self, request, pk):
        try:
            user = Usuario.objects.get(pk=pk)
        except:
            return Response(
                {"detail": f"Usuário com id: {pk}, não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if user.id != request.user.pk and not request.user.is_superuser:
            return response.not_admin_user()

        user.is_active = False
        user.save()
        return Response(status.HTTP_204_NO_CONTENT)


