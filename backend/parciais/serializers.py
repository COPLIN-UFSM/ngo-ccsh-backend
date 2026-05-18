from rest_framework import serializers
from parciais.models import *
from django.db.models import Q

class EmpenhoPagamentoParcialSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpenhoPagamentoParcial
        fields = ["id_empenho", "empenho", "descricao", "ativo", "montante"]
        read_only = ["id_empenho", "ativo", "montante"]


# Aqui é definido qual o tipo do documento: Emepenho, Lista SIAFE, Fatura...
class TipoDocumentoPagamentoParcialSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumentoPagamentoParcial
        fields = ["id_tipo_documento", "tipo_documento", "ativo"]
        read_only = ["id_tipo_documento", "ativo"]


class TransacaoPagamentoParcialSerializer(serializers.ModelSerializer):
    saldo_no_momento = serializers.SerializerMethodField()

    class Meta:
        model = TransacaoPagamentoParcial
        fields = [
            "id_transacao",
            "empenho_pai",
            "tipo_documento",
            "eh_credito",
            "documento",
            "descricao",
            "data_lancamento",
            "montante",
            "saldo_no_momento",
        ]
        read_only_fields = ["data_lancamento"]

    def get_saldo_no_momento(self, data):
        history = TransacaoPagamentoParcial.objects.filter(
            empenho_pai=data.empenho_pai,
            id_transacao__lte=data.id_transacao,
            # data_lancamento__lte=data.data_lancamento,
        ).aggregate(
            creditos=Sum("montante", filter=Q(eh_credito=True), default=0),
            debitos=Sum("montante", filter=Q(eh_credito=False), default=0),
        )
        saldo = (history["creditos"] or Decimal(0)) - (history["debitos"] or Decimal(0))
        return saldo

    def validate(self, data):
        empenho = data.get("empenho_pai")
        eh_credito = data.get("eh_credito")
        montante_novo = data.get("montante")

        if empenho:
            if not empenho.ativo:
                raise serializers.ValidationError(
                    {
                        "empenho_pai": "Não é possível lançar transações em um empenho inativo."
                    }
                )
            if not eh_credito and montante_novo > empenho.montante:
                raise serializers.ValidationError({"montante": "Saldo insuficiente."})
        return data
