from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .serializers import UserListSerializer, UserDetailsSerializer, ChangePasswordSerializer

from utils import response
from usuarios.models import Usuario


class UserListView(APIView):
    """
    View para listar usuários e criar um novo usuário
    """
    serializer_class = UserListSerializer

    @extend_schema(
        summary="Lista usuários",
        description="Retorna a lista de usuários, ativos ou inativos",
        responses={
            200: OpenApiResponse(description="Lista de usuários retornada com sucesso"),
            401: OpenApiResponse(description="Usuário não autenticado"),
        },
        tags=["usuários"],
    )
    def get(self, request):
        # TODO adicionar depois possibilidade de filtrar!
        users = Usuario.objects.all().order_by('id')
        serializer = self.serializer_class(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cria novo usuário",
        description="Cria um novo usuário. Disponível apenas para administradores",
        responses={
            201: OpenApiResponse(description="Usuário criado com sucesso"),
            400: OpenApiResponse(description="Dados inválidos para criação do usuário"),
            403: OpenApiResponse(description="Apenas administradores podem criar usuários"),
        },
        tags=["usuários"],
    )
    def post(self, request):
        if not request.user.is_superuser:
            return response.not_admin_user()

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return response.created("Usuário criado com sucesso.")


class UserDetailsView(APIView):
    """Retorna informações sobre um usuário em específico, dado seu ID"""

    serializer_class = UserDetailsSerializer

    @extend_schema(
        summary="Busca usuário",
        description="Retorna os dados de um usuário pelo ID.",
        parameters=[
            OpenApiParameter(
                name="id_usuario",
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
        tags=["usuários"],
    )
    def get(self, request, id_usuario):
        """
        Mostra dados de um usuário
        """
        try:
            user = Usuario.objects.get(id=id_usuario)
        except Usuario.DoesNotExist:
            return Response(
                {"detail": f"Usuário com id: {id_usuario}, não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Atualiza dados de um usuário",
        description="Atualiza parcialmente os dados de um usuário pelo ID.",
        parameters=[
            OpenApiParameter(
                name="id_usuario",
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
        tags=["usuários"],
    )
    def patch(self, request, id_usuario):
        try:
            user = Usuario.objects.get(id=id_usuario)
        except Usuario.DoesNotExist:
            return Response(
                {"detail": f"Usuário com não encontrado!"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        changes = dict()
        for field, value in serializer.validated_data.items():
            if getattr(user, field) != value:
                changes[field] = value

        if not changes:
            return Response(
                {"detail": f"Nenhuma mudança realizada."},
                status.HTTP_200_OK,
            )

        if not not request.user.is_superuser:
            if user.id != request.user.id:
                return Response(
                    {"detail": "Não é possível alterar dados de outro usuário sem ser administrador."},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif 'is_superuser' in changes:
                return Response(
                    {"detail": "Não é possível conceder-se privilégio de administrador sem ser administrador!"},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif 'is_active' in changes:
                return Response(
                    {"detail": "Apenas um administrador pode desativar sua conta!"},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer.save()
        return Response(
            {"detail": "Campos atualizado com sucesso.", "changes": changes},
            status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Desativa usuário",
        description="Desativa um usuário utilizando seu ID.",
        parameters=[
            OpenApiParameter(
                name="id_usuario",
                type=int,
                location="path",
                description="ID do usuário a ser desativado",
                required=True,
            )
        ],
        responses={
            204: OpenApiResponse(description="Usuário desativado com sucesso"),
            401: OpenApiResponse(description="Não é possível desativar este usuário"),
            404: OpenApiResponse(description="Usuário não encontrado"),
        },
        tags=["usuários"],
    )
    def delete(self, request, id_usuario):
        try:
            user = Usuario.objects.get(id=id_usuario)
        except Usuario.DoesNotExist:
            return Response(
                {"detail": f"Usuário com id: {id_usuario}, não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.id != request.user.id and not request.user.is_superuser:
            return response.not_admin_user()

        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    @extend_schema(
        summary="Altera senha",
        description="Altera a senha de um usuário autenticado por ID.",
        parameters=[
            OpenApiParameter(
                name="id_usuario",
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
        tags=["usuários"],
    )
    def patch(self, request, *args, **kwargs):
        id_usuario = kwargs['id_usuario']

        try:
            user = Usuario.objects.get(id=id_usuario)
        except Usuario.DoesNotExist:
            return Response(
                {'detail': 'Usuário não encontrado!'}, status=status.HTTP_404_NOT_FOUND
            )

        is_admin = request.user.is_superuser
        changing_other = id_usuario != request.user.id

        if not is_admin and changing_other:
            return Response(
                {'detail': 'Apenas administradores podem trocar a senha de outros usuários.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data["password1"])
        user.save()

        return Response(
            {"detail": "Senha atualizada com sucesso!"},
            status=status.HTTP_200_OK,
        )
