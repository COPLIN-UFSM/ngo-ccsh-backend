from rest_framework.response import Response
from rest_framework import status


def response_not_admin_user():
    return Response(
        {"detail": "Apenas administradores podem fazer esta operação"},
        status=status.HTTP_401_UNAUTHORIZED,
    )


def response_error_server():
    return Response(
        {"detail": "Algum erro aconteceu durante a operação."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def response_success_post(table_name):
    return Response(
        {"detail": f"{table_name} adicionado com sucesso!"},
        status=status.HTTP_200_OK,
    )


def response_serializer_errors(serializer):
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
