from despesas import saldos
from despesas.serializers_saldos import UnidadeComSaldoSerializer
from despesas.views.centros import _SaldoViewSetMixin
from entidades.models import Unidade
from rest_framework import viewsets


class UnidadeSaldoViewSet(_SaldoViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = (
        Unidade.objects.all()
        .select_related("centro", "tipo_unidade", "situacao_unidade", "unidade_pai")
        .order_by("id_unidade_interna")
    )
    serializer_class = UnidadeComSaldoSerializer
    filterset_fields = ["centro", "id_unidade_interna"]

    def _filtrar_por_saldo_minimo(self, queryset, ano_fiscal, saldo_minimo):
        return saldos.filtrar_unidades_por_saldo_minimo(
            queryset, ano_fiscal, saldo_minimo
        )
