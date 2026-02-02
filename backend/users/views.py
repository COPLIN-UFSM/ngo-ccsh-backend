# Create your views here.
from ssl import ALERT_DESCRIPTION_ACCESS_DENIED
import stat
from psycopg2 import apilevel
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer

from .models import CustomUser

from .services import enviar_email_recuperacao

# Autenticacao + JWT
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication


# Token acesso único -> Para criar mudança de senha quando se esqueceu a senha!!!
from django.contrib.auth.tokens import (
    default_token_generator,
)  # Token de acesso único, pesquisa sobre;;
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model


from rest_framework.decorators import api_view, permission_classes


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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


class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id_user):
        # Mudar para id_usuario, quando mudar o id
        if id_user != request.user.id:
            return Response(
                {"detail": "Não é possível alterar dados de outro usuário."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user = CustomUser.objects.filter(pk=id_user)
        if not user:
            return Response(
                {"detail": "Usuário não cadastrado."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = RegisterSerializer(instance=user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(
            {"detail": "Usuário atualizado com sucesso."}, status=status.HTTP_200_OK
        )

    def delete(self, request, id_user):
        if id_user != request.user.id:
            return Response(
                {"detail": "Não é possível alterar dados de outro usuário."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = CustomUser.objects.filter(pk=id_user)
        if not user:
            return Response(
                {"detail": "Usuário não cadastrado."}, status=status.HTTP_404_NOT_FOUND
            )
        user.is_active = False
        
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def list_users(request):
    if request.method == "GET":
        users = CustomUser.objects.filter(is_active=True)
        serializer = RegisterSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Usuário cadastrado com sucesso."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
@api_view(["PATCH", "DELETE"])
def user_details(request, pk):

    try:
        user = CustomUser.objects.get(pk=pk)
    except CustomUser.DoesNotExist:
        return Response(
            {"detail": f"Usuário {pk} não encontrado."},
            status.HTTP_404_NOT_FOUND,
        )

    if user.username != request.user.username:
        return Response(
            {"detail": f"Não é possível alterar dados de outro usuário."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if request.method == "PATCH":
        serializer = RegisterSerializer(user, data=request.data, partial=True)
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

    elif request.method == "DELETE":
        user.is_active = False
        user.save()
        return Response(
            {"detail": "Usuário desativado com sucesso."}, status.HTTP_200_OK
        )
