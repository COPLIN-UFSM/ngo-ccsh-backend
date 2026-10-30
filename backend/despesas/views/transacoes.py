from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from despesas.models import TipoMovimento, Transacao
from despesas.serializers import (
    TipoMovimentoSerializer,
    TransacaoCorrecaoSerializer,
    TransacaoOperationSerializer,
    TransacaoReadSerializer,
)


class TransacoesViewSet(viewsets.ModelViewSet):
    queryset = Transacao.objects.select_related(
        "usuario", "beneficiario", "corrige"
    ).prefetch_related("lancamentos", "documentos")
    serializer_class = TransacaoReadSerializer
    http_method_names = ["get", "post"]
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ["operacao", "data", "usuario", "beneficiario"]
    ordering_fields = ["id_transacao", "data", "criada_em"]
    ordering = ["-data", "-id_transacao"]

    def create(self, request, *args, **kwargs):
        operation = TransacaoOperationSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        operation.is_valid(raise_exception=True)
        transacao = operation.save()
        result = self.get_serializer(transacao)
        return Response(
            result.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(result.data),
        )

    @action(detail=True, methods=["post"], url_path="corrigir")
    def corrigir(self, request, pk=None):
        transacao = self.get_object()
        correction = TransacaoCorrecaoSerializer(data=request.data)
        correction.is_valid(raise_exception=True)
        nova_transacao = correction.save(transacao=transacao, usuario=request.user)
        return Response(
            self.get_serializer(nova_transacao).data,
            status=status.HTTP_201_CREATED,
        )


class TipoMovimentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TipoMovimento.objects.all().order_by("id_tipo_movimento")
    serializer_class = TipoMovimentoSerializer
