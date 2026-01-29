from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status


def home(request):
    return Response(
        {"detail": "Por enquanto ta tudo tranquilo."}, status=status.HTTP_200_OK
    ) 