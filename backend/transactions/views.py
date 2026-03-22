from math import e
import stat

from rest_framework.response import Response
from rest_framework import status

from transactions.serializers import *
from .models import Finalidades, Transacoes
from django.db.models import Avg, Count, Min, Sum
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from utils.response import *


@api_view(["GET"])
@permission_classes([AllowAny])
def home(request):
    return Response(
        {"detail": "Por enquanto ta tudo tranquilo."}, status=status.HTTP_200_OK
    )


class SubtipoFinalidadeView(APIView):
    permission_classes = [IsAuthenticated]
    table_name = "Subtipo de Finalidade"

    def get(self, request):
        subtipos = SubtipoFinalidades.objects.all()
        serializer = SubtipoFinalidadeSerializer(subtipos, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_superuser:
            return response_not_admin_user()
        try:
            serializer = SubtipoFinalidadeSerializer(data=request.data)
            if not serializer.is_valid():
                return response_serializer_errors(serializer=serializer)

            serializer.save()
            return response_success_post(self.table_name)

        except Exception as e:
            print(e)
            return response_error_server()


class FinalidadesView(APIView):
    permission_classes = [IsAuthenticated]
    table_name = "Finalidade"

    def get(self, request):
        data = Finalidades.objects.all()
        serializer = FinalidadesSerializer(data, many=True)
        return Response(serializer.data)

    def post(self, request):

        if not request.user.is_superuser:
            return response_not_admin_user()

        try:
            serializer = FinalidadesSerializer(data=request.data)

            if not serializer.is_valid():
                return response_serializer_errors(serializer=serializer)

            serializer.save()
            return response_success_post(self.table_name)

        except:
            return response_error_server()
