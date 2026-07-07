from rest_framework import viewsets

from entidades.models import Cargo, Discente, Servidor, SituacaoUnidade, Curso, TipoUnidade
from entidades.serializers import (
    CargoSerializer,
    TipoUnidadeSerializer,
    CursoSerializer,
    SituacaoUnidadeSerializer,
    ServidorSerializer,
    DiscenteSerializer
)


# apenas leitura
class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    http_method_names = ["get"]


class TipoUnidadeViewSet(viewsets.ModelViewSet):
    queryset = TipoUnidade.objects.all()
    serializer_class = TipoUnidadeSerializer
    http_method_names = ["get"]


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    http_method_names = ["get"]


class SituacaoUnidadeViewSet(viewsets.ModelViewSet):
    queryset = SituacaoUnidade.objects.all()
    serializer_class = SituacaoUnidadeSerializer
    http_method_names = ["get"]


class ServidorViewSet(viewsets.ModelViewSet):
    queryset = Servidor.objects.all()
    serializer_class = ServidorSerializer
    http_method_names = ["get"]


class DiscenteViewSet(viewsets.ModelViewSet):
    queryset = Discente.objects.all()
    serializer_class = DiscenteSerializer
    http_method_names = ["get"]

