from entidades.models import Centro, Unidade
from entidades.serializers import CentroSerializer, UnidadeSerializer
from rest_framework import serializers

from despesas import saldos
from despesas.models import ZERO, Natureza


def _valor(value):
    return f"{value:.2f}"


class UnidadeSaldoSerializer(serializers.Serializer):
    id_natureza = serializers.IntegerField()
    natureza = serializers.CharField()
    orcamento = serializers.DecimalField(max_digits=15, decimal_places=2)
    alocado = serializers.DecimalField(max_digits=15, decimal_places=2)
    entrada = serializers.DecimalField(max_digits=15, decimal_places=2)
    recebido = serializers.DecimalField(max_digits=15, decimal_places=2)
    transferido = serializers.DecimalField(max_digits=15, decimal_places=2)
    gasto = serializers.DecimalField(max_digits=15, decimal_places=2)
    saldo = serializers.DecimalField(max_digits=15, decimal_places=2)
    saldo_projetado = serializers.DecimalField(max_digits=15, decimal_places=2)


class CentroSaldoSerializer(serializers.Serializer):
    id_natureza = serializers.IntegerField()
    natureza = serializers.CharField()
    orcamento = serializers.DecimalField(max_digits=15, decimal_places=2)
    gasto = serializers.DecimalField(max_digits=15, decimal_places=2)
    empenhado = serializers.DecimalField(max_digits=15, decimal_places=2)
    saldo = serializers.DecimalField(max_digits=15, decimal_places=2)
    saldo_projetado = serializers.DecimalField(max_digits=15, decimal_places=2)
    distribuido_unidades = serializers.DecimalField(max_digits=15, decimal_places=2)
    nao_distribuido_unidades = serializers.DecimalField(max_digits=15, decimal_places=2)


class _SaldoListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        iterable = data.all() if hasattr(data, "all") else data
        instances = list(iterable)
        if instances:
            self.child._preparar_saldos(instances)
        return super().to_representation(instances)


class _SaldoSerializerMixin:
    def _preparar_saldos(self, instances):
        self._naturezas_saldo = list(_naturezas())
        self._saldos_calculados = self._calcular_saldos(
            [instance.pk for instance in instances],
            self.context["ano_fiscal"],
            [natureza.pk for natureza in self._naturezas_saldo],
        )

    def _obter_saldos(self, instance):
        if not hasattr(self, "_saldos_calculados"):
            self._preparar_saldos([instance])
        return self._serializar_saldos(
            instance, self._naturezas_saldo, self._saldos_calculados
        )


class CentroComSaldoSerializer(_SaldoSerializerMixin, CentroSerializer):
    ano_fiscal = serializers.IntegerField(read_only=True)
    saldos = CentroSaldoSerializer(many=True, read_only=True)

    class Meta(CentroSerializer.Meta):
        fields = list(CentroSerializer.Meta.fields) + ["ano_fiscal", "saldos"]
        list_serializer_class = _SaldoListSerializer

    def to_representation(self, instance: Centro):
        data = super().to_representation(instance)
        data["ano_fiscal"] = self.context["ano_fiscal"]
        data["saldos"] = self._obter_saldos(instance)
        return data

    def _calcular_saldos(self, centro_ids, ano_fiscal, natureza_ids):
        return saldos.saldos_centros(centro_ids, ano_fiscal, natureza_ids)

    def _serializar_saldos(self, centro, naturezas, saldos_calculados):
        return _saldos_centro(centro, naturezas, saldos_calculados)


class UnidadeComSaldoSerializer(_SaldoSerializerMixin, UnidadeSerializer):
    ano_fiscal = serializers.IntegerField(read_only=True)
    saldos = UnidadeSaldoSerializer(many=True, read_only=True)

    class Meta(UnidadeSerializer.Meta):
        fields = list(UnidadeSerializer.Meta.fields) + ["ano_fiscal", "saldos"]
        list_serializer_class = _SaldoListSerializer

    def to_representation(self, instance: Unidade):
        data = super().to_representation(instance)
        data["ano_fiscal"] = self.context["ano_fiscal"]
        data["saldos"] = self._obter_saldos(instance)
        return data

    def _calcular_saldos(self, unidade_ids, ano_fiscal, natureza_ids):
        return saldos.saldos_unidades(unidade_ids, ano_fiscal, natureza_ids)

    def _serializar_saldos(self, unidade, naturezas, saldos_calculados):
        return _saldos_unidade(unidade, naturezas, saldos_calculados)


def _naturezas():
    return Natureza.objects.filter(ativo=True).order_by("id_natureza")


def _saldos_unidade(unidade: Unidade, naturezas, saldos_calculados):
    resultado = []
    for natureza in naturezas:
        valores = saldos_calculados.get((unidade.pk, natureza.pk), {})
        gasto = valores.get("gasto", ZERO)
        saldo = valores.get("saldo", ZERO)
        alocado = valores.get("alocado", ZERO)
        resultado.append(
            {
                "id_natureza": natureza.pk,
                "natureza": natureza.nome,
                "orcamento": _valor(saldo + gasto),
                "alocado": _valor(alocado),
                "entrada": _valor(valores.get("entrada", ZERO)),
                "recebido": _valor(valores.get("recebido", ZERO)),
                "transferido": _valor(valores.get("transferido", ZERO)),
                "gasto": _valor(gasto),
                "saldo": _valor(saldo),
                "saldo_projetado": _valor(saldo - alocado),
            }
        )
    return resultado


def _saldos_centro(centro: Centro, naturezas, saldos_calculados):
    resultado = []
    for natureza in naturezas:
        valores = saldos_calculados.get((centro.pk, natureza.pk), {})
        orcamento = valores.get("orcamento", ZERO)
        gasto = valores.get("gasto", ZERO)
        empenhado = valores.get("empenhado", ZERO)
        distribuido = valores.get("distribuido_unidades", ZERO)
        resultado.append(
            {
                "id_natureza": natureza.pk,
                "natureza": natureza.nome,
                "orcamento": _valor(orcamento),
                "gasto": _valor(gasto),
                "empenhado": _valor(empenhado),
                "saldo": _valor(orcamento - gasto),
                "saldo_projetado": _valor(orcamento - gasto - empenhado),
                "distribuido_unidades": _valor(distribuido),
                "nao_distribuido_unidades": _valor(orcamento - distribuido),
            }
        )
    return resultado
