# Create your views here.
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

# Token acesso único
from django.contrib.auth.tokens import default_token_generator #Token de acesso único, pesquisa sobre;;
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Usuário criado com Sucesso."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )



# class ForgotPasswordView(APIView):
# permission_classes = [AllowAny]

# def post(self, request):
#     email = request.data.get("email")
#     if not email:
#         return Response(
#             data={"error": "Por favor, insira o email."},
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     user = CustomUser.objects.filter(email=email).first()
#     if user:
#         token = default_token_generator.make_token(user)
#         uid = urlsafe_base64_encode(force_bytes(user.pk))
#         enviar_email_recuperacao(user, uid, token)

#     return Response(
#         {
#             "message": "Se o email estiver cadastrado, você receberá um email para mudar sua senha."
#         },
#         status.HTTP_200_OK,
#     )


class ListUsers(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = RegisterSerializer(users, many=True)

        return Response(serializer.data, status.HTTP_200_OK)


from rest_framework_simplejwt.tokens import RefreshToken


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                data={
                    "error": "Usuário ou senha não preenchidos. Por favor preencha os campos."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                data={"error": "Credências inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if user.is_active:
            refresh = RefreshToken.for_user(user=user)
            return Response(
                data={
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "username": user.get_username(),
                        "email": user.get_email(),
                    },
                },
                status=status.HTTP_200_OK,
            )


class PerfilView(APIView):
    #   authentication_classes = [JWTAuthentication]
    #   permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {"username": request.user.username, "email": request.user.email},
            status.HTTP_200_OK,
        )
