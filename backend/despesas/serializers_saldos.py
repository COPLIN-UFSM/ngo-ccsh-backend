from entidades.models import Centro, Unidade
from entidades.serializers import CentroSerializer, UnidadeSerializer
from rest_framework import serializers

from despesas import saldos
from despesas.models import Natureza


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
    nao_distribuido_unidades = serializers.DecimalField(
        max_digits=15, decimal_places=2
    )


class CentroComSaldoSerializer(CentroSerializer):
    ano_fiscal = serializers.IntegerField(read_only=True)
    saldos = CentroSaldoSerializer(many=True, read_only=True)

    class Meta(CentroSerializer.Meta):
        fields = list(CentroSerializer.Meta.fields) + ["ano_fiscal", "saldos"]

    def to_representation(self, instance: Centro):
        data = super().to_representation(instance)
        data["ano_fiscal"] = self.context["ano_fiscal"]
        data["saldos"] = _saldos_centro(instance, data["ano_fiscal"])
        return data


class UnidadeComSaldoSerializer(UnidadeSerializer):
    ano_fiscal = serializers.IntegerField(read_only=True)
    saldos = UnidadeSaldoSerializer(many=True, read_only=True)

    class Meta(UnidadeSerializer.Meta):
        fields = list(UnidadeSerializer.Meta.fields) + ["ano_fiscal", "saldos"]

    def to_representation(self, instance: Unidade):
        data = super().to_representation(instance)
        data["ano_fiscal"] = self.context["ano_fiscal"]
        data["saldos"] = _saldos_unidade(instance, data["ano_fiscal"])
        return data


def _naturezas():
    return Natureza.objects.filter(ativo=True).order_by("id_natureza")


def _saldos_unidade(unidade: Unidade, ano_fiscal: int):
    resultado = []
    for natureza in _naturezas():
        gasto = saldos.gasto_unidade(unidade.pk, ano_fiscal, natureza.pk)
        saldo = saldos.saldo_unidade(unidade.pk, ano_fiscal, natureza.pk)
        alocado = saldos.alocado_unidade(unidade.pk, ano_fiscal, natureza.pk)
        resultado.append(
            {
                "id_natureza": natureza.pk,
                "natureza": natureza.nome,
                "orcamento": _valor(saldo + gasto),
                "alocado": _valor(alocado),
                "entrada": _valor(
                    saldos.distribuido_unidade(unidade.pk, ano_fiscal, natureza.pk)
                ),
                "recebido": _valor(
                    saldos.recebido_unidade(unidade.pk, ano_fiscal, natureza.pk)
                ),
                "transferido": _valor(
                    saldos.transferido_unidade(unidade.pk, ano_fiscal, natureza.pk)
                ),
                "gasto": _valor(gasto),
                "saldo": _valor(saldo),
                "saldo_projetado": _valor(saldo - alocado),
            }
        )
    return resultado


def _saldos_centro(centro: Centro, ano_fiscal: int):
    resultado = []
    for natureza in _naturezas():
        orcamento = saldos.orcamento_centro(centro.pk, ano_fiscal, natureza.pk)
        gasto = saldos.gasto_centro(centro.pk, ano_fiscal, natureza.pk)
        empenhado = saldos.empenhado_centro(centro.pk, ano_fiscal, natureza.pk)
        distribuido = saldos.distribuido_unidades_centro(
            centro.pk, ano_fiscal, natureza.pk
        )
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
