from rest_framework import serializers
from partial_payments.models import *


class EmpenhoPagamentoParcialSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpenhoPagamentoParcial
        fields = ["id_empenho", "empenho", "descricao", "ativo"]
        read_only = ["id_empenho", "ativo"]


# Aqui é definido qual o tipo do documento: Emepenho, Lista SIAFE, Fatura...
class TipoDocumentoPagamentoParcialSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumentoPagamentoParcial
        fields = ["id_tipo_documento", "tipo_documento", "ativo"]
        read_only = ["id_tipo_documento", "ativo"]


class TransacaoPagamentoParcialSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransacaoPagamentoParcial
        fields = [
            "id_transacao",
            "empenho_pai",
            "tipo_documento",
            "credito",
            "documento",
            "descricao",
            "data_lancamento",
            "montante",
            "ativo",
        ]
        read_only = ["data_lancamento", "ativo"]



# # Aqui é definido se é: Crédito, Débito .
# class TipoTransacaoPagamentoParcialSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TipoTransacaoPagamentoParcial
#         fields = ["id_tipo_transacao", "tipo_transacao", "ativo"]
#         read_only = ["id_tipo_transacao", "ativo"]
