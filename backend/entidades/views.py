from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from entidades.filters import UnidadeFilterSet
from entidades.models import (
    Centro,
    Curso,
    Discente,
    Email,
    Pessoa,
    Servidor,
    SituacaoUnidade,
    Telefone,
    TipoUnidade,
    Unidade,
)
from entidades.serializers import (
    CentroSerializer,
    CursoSerializer,
    DiscenteSerializer,
    EmailSerializer,
    PessoaSerializer,
    ServidorSerializer,
    SituacaoUnidadeSerializer,
    TelefoneSerializer,
    TipoUnidadeSerializer,
    UnidadeSerializer,
)

detailNotAllowed = "Método não permitido para elementos cadastrados no SIE."


class TipoUnidadeViewSet(viewsets.ModelViewSet):
    queryset = TipoUnidade.objects.all()
    serializer_class = TipoUnidadeSerializer
    http_method_names = ["get"]


class SituacaoUnidadeViewSet(viewsets.ModelViewSet):
    queryset = SituacaoUnidade.objects.all()
    serializer_class = SituacaoUnidadeSerializer
    http_method_names = ["get"]


class CentroViewSet(viewsets.ModelViewSet):
    queryset = Centro.objects.all()
    serializer_class = CentroSerializer
    http_method_names = ["get", "post", "patch"]

    def partial_update(self, request, *args, **kwargs):
        centro: Centro = self.get_object()

        if centro.centro_sie is not None:
            raise MethodNotAllowed(detail=detailNotAllowed, method="PATCH")

        serializer = self.get_serializer(centro, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data)


class UnidadeViewSet(viewsets.ModelViewSet):
    queryset = Unidade.objects.all().select_related(
        "centro", "tipo_unidade", "situacao_unidade"
    )
    http_method_names = ["get", "post", "patch"]

    ordering_fields = ["id_grupo_finalidade", "grupo_finalidade"]
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    serializer_class = UnidadeSerializer
    filterset_class = UnidadeFilterSet

    def partial_update(
        self, request: object, *args: object, **kwargs: object
    ) -> Response:
        unidade: Unidade = self.get_object()
        unidade_fields = [
            "id_unidade_interna",
            "nome_unidade",
            "cod_estruturado",
            "id_centro",
            "id_tipo_unidade",
            "id_situacao_unidade",
        ]
        data_sent = request.data.keys()
        field_errors = []
        if unidade.unidade_sie is not None:
            for field in data_sent:
                if field in unidade_fields:
                    field_errors.append(
                        {
                            field: "Este campo não pode ser alterado em uma Unidade do SIE"
                        }
                    )
            if field_errors:
                return Response(field_errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(unidade, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data)


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all().select_related("centro")
    serializer_class = CursoSerializer
    http_method_names = ["get"]

    search_fields = ["nome_curso"]


class PessoaViewSet(viewsets.ModelViewSet):
    queryset = Pessoa.objects.all().prefetch_related("telefone_set", "email_set")
    serializer_class = PessoaSerializer
    http_method_names = ["get", "post", "patch"]

    def partial_update(self, request, *args, **kwargs):
        pessoa = self.get_object()
        if pessoa.pessoa_sie is not None:
            raise MethodNotAllowed(detail=detailNotAllowed, method="PATCH")

        serializer = PessoaSerializer(instance=pessoa, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class DiscenteViewSet(viewsets.ModelViewSet):
    queryset = Discente.objects.all().select_related("pessoa", "curso")
    serializer_class = DiscenteSerializer
    http_method_names = ["get"]


class ServidorViewSet(viewsets.ModelViewSet):
    queryset = Servidor.objects.all().select_related("pessoa", "cargo")
    serializer_class = ServidorSerializer
    http_method_names = ["get"]


class TelefoneViewSet(viewsets.ModelViewSet):
    queryset = Telefone.objects.all()
    serializer_class = TelefoneSerializer
    http_method_names = ["get", "post", "patch", "delete"]


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    http_method_names = ["get", "post", "patch", "delete"]
