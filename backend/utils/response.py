from rest_framework.response import Response
from rest_framework import status


def not_admin_user():
    return Response(
        {"detail": "Apenas administradores podem fazer esta operação"},
        status=status.HTTP_401_UNAUTHORIZED,
    )


def not_found(message):
    return Response(
        {"detail": message},
        status=status.HTTP_404_NOT_FOUND,
    )


def error_server(error=None):
    if error is None:
        return Response(
            {"detail": "Algum erro aconteceu durante a operação."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response(
        {
            "detail": f"Algum erro aconteceu durante a operação: {error} ",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def bad_request(message):
    return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)


def success_data(data):
    return Response(
        {"data": data},
        status=status.HTTP_200_OK,
    )


def success_no_content():
    return Response(status=status.HTTP_204_NO_CONTENT)


def success(message):
    return Response(
        {"detail": message},
        status=status.HTTP_200_OK,
    )


def serializer_errors(serializer):
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
