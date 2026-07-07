from rest_framework import viewsets

from entidades.models import (
    Discente,
    Servidor,
    SituacaoUnidade,
    Curso,
    TipoUnidade,
    Centro,
    Pessoa,
    Unidade
)

from entidades.serializers import (
    CentroSerializer,
    TipoUnidadeSerializer,
    CursoSerializer,
    SituacaoUnidadeSerializer,
    ServidorSerializer,
    DiscenteSerializer,
    PessoaSerializer, UnidadeSerializer
)


class CentroViewSet(viewsets.ModelViewSet):
    queryset = Centro.objects.all()
    serializer_class = CentroSerializer
    http_method_names = ["get"]
    # TODO depende se pode mexer! se tiver id_centro_sie, não pode mexer. do contrário, pode


class UnidadeViewSet(viewsets.ModelViewSet):
    queryset = Unidade.objects.all()
    serializer_class = UnidadeSerializer
    http_method_names = ["get"]
    # TODO depende se pode mexer! se tiver id_unidade_sie, não pode mexer. do contrário, pode
    # TODO mostrar centro
    # TODO mostrar situacaoUnidade
    # TODO mostrar tipoUnidade


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    http_method_names = ["get"]


class PessoaViewSet(viewsets.ModelViewSet):
    queryset = Pessoa.objects.all()
    serializer_class = PessoaSerializer
    # TODO depende se pode mexer! se tiver id_centro_sie, não pode mexer. do contrário, pode
    # TODO mostrar e-mail e telefone

class DiscenteViewSet(viewsets.ModelViewSet):
    queryset = Discente.objects.all()
    serializer_class = DiscenteSerializer
    http_method_names = ["get"]
    # TODO mostrar e-mail e telefone
    # TODO mostrar curso


class ServidorViewSet(viewsets.ModelViewSet):
    queryset = Servidor.objects.all()
    serializer_class = ServidorSerializer
    http_method_names = ["get"]
    # TODO mostrar e-mail e telefone
    # TODO mostrar cargo
