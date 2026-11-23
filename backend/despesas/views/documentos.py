from despesas.filters import LancamentoFilterSet, TipoDocumentoFilterSet
from despesas.models import Lancamento, TipoDocumento, Transacao, ValorDocumento
from despesas.serializers import (
    LancamentoSerializer,
    TipoDadoDocumentoSerializer,
    TipoDocumentoSerializer,
    ValorDocumentoSerializer,
)
from despesas.views.ativoUtil import AtivoListDefaultMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.filters import AliasOrderingFilter


class TipoDadoDocumentoViewSet(APIView):
    def get(self, request):
        serializer = TipoDadoDocumentoSerializer(instance={})
        return Response(serializer.data)


class TipoDocumentoViewSet(AtivoListDefaultMixin, viewsets.ModelViewSet):
    queryset = TipoDocumento.objects.all().order_by("id_tipo_documento")
    serializer_class = TipoDocumentoSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = TipoDocumentoFilterSet
    ordering_fields = ["id_tipo_documento", "nome"]
    http_method_names = ["get", "post", "patch", "delete"]


class ValorDocumentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ValorDocumento.objects.select_related("tipo_documento")
    serializer_class = ValorDocumentoSerializer

    def get_queryset(self):
        transacao_id = self.kwargs.get("transacao_pk")
        if not Transacao.objects.filter(pk=transacao_id).exists():
            raise NotFound(detail="Transação não encontrada.")
        return self.queryset.filter(transacao_id=transacao_id)


class LancamentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lancamento.objects.select_related(
        "tipo_movimento", "natureza", "finalidade"
    )
    serializer_class = LancamentoSerializer
    filter_backends = (DjangoFilterBackend, AliasOrderingFilter)
    filterset_class = LancamentoFilterSet
    ordering_fields = [
        "id_lancamento",
        "id_empenho",
        "id_unidade",
        "ano_fiscal",
        "natureza",
        "tipo_movimento",
        "finalidade",
        "montante",
    ]
    ordering_aliases = {
        "id_empenho": "empenho_id",
        "id_unidade": "unidade_id",
        "natureza": "natureza__nome",
        "tipo_movimento": "tipo_movimento__nome",
        "finalidade": "finalidade__nome",
    }

    def get_queryset(self):
        transacao_id = self.kwargs.get("transacao_pk")
        if not Transacao.objects.filter(pk=transacao_id).exists():
            raise NotFound(detail="Transação não encontrada.")
        return self.queryset.filter(transacao_id=transacao_id).order_by("id_lancamento")
