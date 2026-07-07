from django.http import Http404
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.response import Response

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
    http_method_names = ["get", "post", "patch"]
    # OK ?
    # TODO depende se pode mexer! se tiver centro_sie, não pode mexer. do contrário, pode

    def partial_update(self,req, *args, **kwargs):
        centro = self.get_object()

        if centro.centro_sie is not None:
            raise MethodNotAllowed(detail="Método não permitido para centros cadastrados no sie", method="PATCH")

        serializer = self.get_serializer(centro, data=req.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data)



class UnidadeViewSet(viewsets.ModelViewSet):
    queryset = Unidade.objects.all().select_related("centro", "tipo_unidade", "situacao_unidade")
    serializer_class = UnidadeSerializer
    http_method_names = ["get","post","patch"]

    # OK?
    # TODO depende se pode mexer! se tiver id_unidade_sie, não pode mexer. do contrário, pode
    # TODO mostrar centro
    # TODO mostrar situacaoUnidade
    # TODO mostrar tipoUnidade
    def partial_update(self,req, *args, **kwargs):
        unidade = self.get_object()

        if unidade.centro_sie is not None:
            raise MethodNotAllowed(detail="Método não permitido para unidades cadastrados no sie", method="PATCH")

        serializer = self.get_serializer(unidade, data=req.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data)



class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    http_method_names = ["get"]
    # !OK


class PessoaViewSet(viewsets.ModelViewSet):
    queryset = Pessoa.objects.all()
    serializer_class = PessoaSerializer
    # TODO depende se pode mexer! se tiver id_pessoa_sie, não pode mexer. do contrário, pode
    # TODO mostrar e-mail e telefone

class DiscenteViewSet(viewsets.ModelViewSet):
    queryset = Discente.objects.all().select_related('email', 'curso')
    serializer_class = DiscenteSerializer
    http_method_names = ["get"]
    # !OK
    # TODO mostrar e-mail e telefone
    # TODO mostrar curso


class ServidorViewSet(viewsets.ModelViewSet):
    queryset = Servidor.objects.all().select_related('email', 'curso', 'cargo')
    serializer_class = ServidorSerializer
    http_method_names = ["get"]
    # !OK
    # TODO mostrar e-mail e telefone
    # TODO mostrar cargo
