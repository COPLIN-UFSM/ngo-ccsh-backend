from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from despesas.models import TipoDocumento, ValorDocumento
from despesas.serializers import DocumentoSerializer, TipoDocumentoSerializer


class TipoDocumentoViewSet(viewsets.ModelViewSet):
    queryset = TipoDocumento.objects.all()
    serializer_class = TipoDocumentoSerializer

    def get_queryset(self):
        return TipoDocumento.objects.filter(ativo=True)

    def get_permissions(self):
        return [IsAuthenticated()]
    
    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save()

class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = ValorDocumento.objects.all()
    serializer_class = DocumentoSerializer

    def get_queryset(self):
        return ValorDocumento.objects.filter()
    
    def get_permissions(self):
        return [IsAuthenticated()]
    