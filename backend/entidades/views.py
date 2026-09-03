from rest_framework import viewsets
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response

from entidades.models import (
    Discente,
    Servidor,
    SituacaoUnidade,
    Curso,
    TipoUnidade,
    Centro,
    Pessoa,
    Unidade, Telefone, Email
)
from entidades.serializers import (
    CentroSerializer,
    TipoUnidadeSerializer,
    CursoSerializer,
    SituacaoUnidadeSerializer,
    ServidorSerializer,
    DiscenteSerializer,
    PessoaSerializer, UnidadeSerializer, TelefoneSerializer, EmailSerializer
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
    queryset = Unidade.objects.all().select_related("centro", "tipo_unidade", "situacao_unidade")
    serializer_class = UnidadeSerializer
    http_method_names = ["get", 'post', "patch"]

    def partial_update(self, request: object, *args: object, **kwargs: object) -> Response:
        unidade: Unidade = self.get_object()

        if unidade.unidade_sie is not None:
            raise MethodNotAllowed(detail=detailNotAllowed, method="PATCH")

        serializer = self.get_serializer(unidade, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data)


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all().select_related('centro')
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
    queryset = Discente.objects.all().select_related('pessoa', 'curso')
    serializer_class = DiscenteSerializer
    http_method_names = ["get"]


class ServidorViewSet(viewsets.ModelViewSet):
    queryset = Servidor.objects.all().select_related('pessoa', 'cargo')
    serializer_class = ServidorSerializer
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = super().get_queryset()

        cpf = self.request.query_params.get("cpf")

        if cpf:
            queryset = self._filtrar_por_cpf(queryset, cpf)
        else:
            queryset = self._filtrar_por_ativo_padrao(queryset)

        # 'ativo' explícito sempre pode ser aplicado, com ou sem cpf
        queryset = self._filtrar_por_ativo_explicito(queryset)

        return queryset

    def _filtrar_por_ativo_padrao(self, queryset):
        # Sem cpf: comportamento de listagem, só ativos por padrão
        if self.request.query_params.get("ativo") is None:
            return queryset.filter(ativo=True)
        return queryset

    def _filtrar_por_ativo_explicito(self, queryset):
        ativo_param = self.request.query_params.get("ativo")
        if ativo_param is None:
            return queryset

        ativo_bool = ativo_param.strip().lower() in ("true", "1")
        return queryset.filter(ativo=ativo_bool)

    @staticmethod
    def _filtrar_por_cpf(queryset, cpf):
        cpf_normalizado = "".join(filter(str.isdigit, cpf))

        if len(cpf_normalizado) != 11:
            return queryset.none()

        try:
            pessoa = Pessoa.objects.get(cpf=cpf_normalizado)
        except Pessoa.DoesNotExist:
            return queryset.none()
        except Pessoa.MultipleObjectsReturned:
            pessoa = Pessoa.objects.filter(cpf=cpf_normalizado).first()

        return queryset.filter(pessoa=pessoa)


class TelefoneViewSet(viewsets.ModelViewSet):
    queryset = Telefone.objects.all()
    serializer_class = TelefoneSerializer
    http_method_names = ["get", "post", "patch", "delete"]


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    http_method_names = ["get", "post", "patch", "delete"]
