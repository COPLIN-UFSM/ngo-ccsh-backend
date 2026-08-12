from rest_framework.response import Response
from rest_framework import status, viewsets

from despesas.serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from utils import response
from utils.pagination import PaginationWithSize
from rest_framework.exceptions import NotFound

class NaturezaFinalidadeViewSet(viewsets.ModelViewSet):
    queryset = NaturezaFinalidade.objects.all()
    serializer_class = NaturezaFinalidadeSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return NaturezaFinalidade.objects.filter(ativo=True)

    def destroy(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            natureza_finalidade = NaturezaFinalidade.objects.get(pk=pk, ativo=True)
            natureza_finalidade.ativo = False
            natureza_finalidade.save()
            return response.success_no_content()

        except NaturezaFinalidade.DoesNotExist:
            return response.not_found(f"Natureza de finalidade não encontrada")

class GrupoFinalidadeViewSet(viewsets.ModelViewSet):
    queryset = GrupoFinalidade.objects.filter(ativo=True)
    serializer_class = GrupoFinalidadeSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return GrupoFinalidade.objects.filter(ativo=True)

    def destroy(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            grupo_finalidade = GrupoFinalidade.objects.get(pk=pk, ativo=True)
            grupo_finalidade.ativo = False
            grupo_finalidade.save()
            return response.success_no_content()
        except GrupoFinalidade.DoesNotExist:
            return response.not_found("Grupo de finalidade não encontrado")

class FinalidadeViewSet(viewsets.ModelViewSet):
    queryset = Finalidade.objects.all().select_related()
    serializer_class = FinalidadeSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return Finalidade.objects.filter(ativo=True)

    def destroy(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            finalidade = Finalidade.objects.get(pk=pk, ativo=True)
            finalidade.ativo = False
            return response.success_no_content()
        except Finalidade.DoesNotExist:
            return response.not_found("Finalidade não encontrada")