from despesas.filters import EmpenhoFilterSet
from despesas.models import ZERO, Empenho, Lancamento, ParcelaBolsa
from despesas.serializers import EmpenhoSerializer
from despesas.views.ativoUtil import AtivoListDefaultMixin
from django.db.models import DecimalField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter


class EmpenhoViewSet(AtivoListDefaultMixin, viewsets.ModelViewSet):
    queryset = Empenho.objects.select_related(
        "centro", "natureza", "finalidade", "empenho_origem"
    )
    serializer_class = EmpenhoSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = EmpenhoFilterSet
    ordering_fields = ["id_empenho", "numero_empenho", "ano_fiscal"]
    ordering = ["-ano_fiscal", "numero_empenho"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        decimal_field = DecimalField(max_digits=15, decimal_places=2)
        lancamentos = Lancamento.objects.filter(empenho_id=OuterRef("pk")).order_by()
        saldo = (
            lancamentos.values("empenho_id")
            .annotate(total=Sum("montante"))
            .values("total")[:1]
        )
        gasto = (
            lancamentos.filter(tipo_movimento__conta_como_gasto=True)
            .values("empenho_id")
            .annotate(total=Sum("montante"))
            .values("total")[:1]
        )
        previsto = (
            ParcelaBolsa.objects.filter(
                empenho_previsto_id=OuterRef("pk"),
                status=ParcelaBolsa.Status.ALOCADA,
            )
            .order_by()
            .values("empenho_previsto_id")
            .annotate(total=Sum("valor"))
            .values("total")[:1]
        )

        return (
            super()
            .get_queryset()
            .annotate(
                saldo_agregado=Coalesce(
                    Subquery(saldo, output_field=decimal_field),
                    Value(ZERO, output_field=decimal_field),
                    output_field=decimal_field,
                ),
                gasto_agregado=Coalesce(
                    Subquery(gasto, output_field=decimal_field),
                    Value(ZERO, output_field=decimal_field),
                    output_field=decimal_field,
                ),
                previsto_agregado=Coalesce(
                    Subquery(previsto, output_field=decimal_field),
                    Value(ZERO, output_field=decimal_field),
                    output_field=decimal_field,
                ),
            )
        )
