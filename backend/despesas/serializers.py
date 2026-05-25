from rest_framework import serializers
from despesas.models import *


class BeneficiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiario
        fields = ["id_beneficiario", "nome_beneficiario", "cpf", "matricula"]
        read_only_fields = ["id_beneficiario"]


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = ["id_documento", "tipo_documento", "transacao", "descricao"]
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

    natureza_finalidade_detail = NaturezaFinalidadeSerializer(
        source="natureza_finalidade", read_only=True
    )
    tipo_finalidade_detail = TipoFinalidadeSerializer(
        source="tipo_finalidade", read_only=True
    )

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
