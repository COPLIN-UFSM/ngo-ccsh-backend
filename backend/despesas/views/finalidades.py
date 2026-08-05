from rest_framework.viewsets import ModelViewSet

from despesas.serializers import NaturezaFinalidadeSerializer, GrupoFinalidadeSerializer, FinalidadeSerializer
from despesas.models import NaturezaFinalidade, GrupoFinalidade, Finalidade
class NaturezaFinalidadeViewSet(ModelViewSet):
    queryset = NaturezaFinalidade.objects.all()
    serializer_class = NaturezaFinalidadeSerializer
    allowed_methods =['GET', 'POST', 'PUT', 'DELETE']

    def get_queryset(self):
        return NaturezaFinalidade.objects.filter(ativo=True)

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save()

class GrupoFinalidadeViewSet(ModelViewSet):
    queryset = GrupoFinalidade.objects.all()
    serializer_class = GrupoFinalidadeSerializer
    allowed_methods =  ['GET', 'POST', 'PUT', 'DELETE']

    def get_queryset(self):
        return GrupoFinalidade.objects.filter(ativo=True)

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save()

class FinalidadeViewSet(ModelViewSet):
    queryset = Finalidade.objects.all().select_related("natureza_finalidade", "grupo_finalidade", "tipos_documentos")
    serializer_class = FinalidadeSerializer
    allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
    def get_queryset(self):
        return Finalidade.objects.filter(ativo=True)

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save()
