from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from despesas.models import TipoDocumento, Documento
from despesas.serializers import DocumentoSerializer, TipoDocumentoSerializer


class TipoDocumentoViewSet(viewsets.ModelViewSet):
    queryset = TipoDocumento.objects.all()
    serializer_class = TipoDocumentoSerializer

    def get_permissions(self):
        return [IsAuthenticated()]


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer

    def get_permissions(self):
        return [IsAuthenticated()]
