from rest_framework import serializers
from despesas.models import *
from django.db.models import Sum, Case, When, F


class BeneficiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiario
        fields = ["id_beneficiario", "nome_beneficiario", "cpf", "matricula"]
        read_only_fields = ["id_beneficiario"]


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = ["id_documento", "tipo_documento", "documento", "transacao", "descricao"]
        read_only_fields = ["id_documento"]


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = ["id_tipo_documento", "tipo_documento"]
        read_only_fields = ["id_tipo_documento"]


class TipoFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoFinalidade
        fields = ["id_tipo_finalidade", "tipo_finalidade"]
        read_only_fields = ["id_tipo_finalidade"]


class NaturezaFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturezaFinalidade
        fields = ["id_natureza_finalidade", "natureza_finalidade"]
        read_only_fields = ["id_natureza_finalidade"]


class FinalidadeSerializer(serializers.ModelSerializer):
    natureza_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=NaturezaFinalidade.objects.all(),
        write_only=True,
        error_messages={
            "does_not_exist": "Código de despesa inexistente.",
            "incorrect_type": "Formato de dado inválido para o tipo de despesa.",
        },
    )

    tipo_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=TipoFinalidade.objects.all(),
        write_only=True,
        error_messages={
            "does_not_exist": "Código da categoria da finalidade inexistente.",
            "incorrect_type": "Formato de dado inválido para a categoria da finalidade.",
        },
    )

    natureza_finalidade_detail = NaturezaFinalidadeSerializer(source="natureza_finalidade", read_only=True)
    tipo_finalidade_detail = TipoFinalidadeSerializer(source="tipo_finalidade", read_only=True)

    class Meta:
        model = Finalidade
        fields = [
            "id_finalidade",
            "finalidade",
            "natureza_finalidade",
            "natureza_finalidade_detail",
            "tipo_finalidade",
            "tipo_finalidade_detail",
            "modalidade",
        ]
        read_only_fields = ["id_finalidade"]


class SubunidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subunidade
        fields = ["id_subunidade", "subunidade", "grupo"]
        read_only_fields = ["id_subunidade"]


class TransacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transacao
        fields = [
            "id_transacao",
            "transacao_pai",
            "empenho",
            "finalidade",
            "subunidade_credora",
            "subunidade_executora",
            "usuario",
            "status",
            "beneficiario",
            "eh_credito",
            "descricao",
            "montante",
            "quantidade",
            "local_trecho",
            "data_lancamento",
            "data_modificacao",
            "motivo_modificacao",
        ]

    def validate(self, data):
        empenho = data.get("empenho")
        montante = data.get("montante")
        id_transacao = data.get("id_transacao")
        eh_credito = data.get("eh_credito")

        queryset = Transacao.objects.filter(empenho=empenho)
        if self.instance:
            queryset = queryset.exclude(id_transacao=id_transacao)

        total_despesas = (
            queryset.aggregate(
                total=Sum(
                    Case(
                        When(eh_credito=True, then=F("montante")),
                        When(eh_credito=False, then=-F("montante")),
                    )
                )
            )["total"]
            or 0.00
        )

        if not eh_credito and montante > total_despesas:
            raise serializers.ValidationError(
                {"montante": f"Saldo insuficiente. O Valor da despesa (R$ {montante:.2f}) é maior que o saldo atual (R$ {total_despesas:.2f})."}
            )
        return data


class EmpenhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empenho
        fields = ["id_empenho", "empenho", "pen", "descricao", "finalidade"]
        read_only_fields = ["id_empenho"]


# Finalidade em empenho? Finalidade em Transação.
