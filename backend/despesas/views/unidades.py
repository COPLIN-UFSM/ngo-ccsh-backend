from despesas import saldos
from despesas.serializers_saldos import UnidadeComSaldoSerializer
from despesas.views.centros import _SaldoViewSetMixin
from entidades.models import Unidade
from rest_framework import viewsets


class UnidadeSaldoViewSet(_SaldoViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = (
        Unidade.objects.all()
        .select_related("centro", "tipo_unidade", "situacao_unidade")
        .order_by("id_unidade_interna")
    )
    serializer_class = UnidadeComSaldoSerializer
    filterset_fields = ["centro", "id_unidade_interna"]

    def _tem_saldo_maior_que(
        self,
        unidade_id,
        ano_fiscal,
        saldo_minimo,
        naturezas,
    ):
        return any(
            saldos.saldo_unidade(unidade_id, ano_fiscal, natureza_id) > saldo_minimo
            for natureza_id in naturezas
        )
