from dataclasses import fields

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
        fields = ["tipo_documento", "tipo_documento", "transacao", "descricao"]
        read_only_fields = ["id_documento"]


class CategoriaFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaFinalidade
        fields = ["id_categoria_finalidade", "categoria_finalidade"]
        read_only_fields = ["id_categoria_finalidade"]


class TipoDespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDespesa
        fields = ["id_tipo_despesa", "tipo_despesa"]
        read_only_fields = ["id_tipo_despesa"]


class FinalidadeSerializer(serializers.ModelSerializer):
    tipo_despesa = serializers.PrimaryKeyRelatedField(
        queryset=TipoDespesa.objects.all(),
        write_only=True,
        error_messages={
            "does_not_exist": "Código de despesa inexistente.",
            "incorrect_type": "Formato de dado inválido para o tipo de despesa.",
        },
    )

    categoria_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaFinalidade.objects.all(),
        write_only=True,
        error_messages={
            "does_not_exist": "Código da categoria da finalidade inexistente.",
            "incorrect_type": "Formato de dado inválido para a categoria da finalidade.",
        },
    )

    tipo_despesa_detail = TipoDespesaSerializer(source="tipo_despesa", read_only=True)
    categoria_finalidade_detail = CategoriaFinalidadeSerializer(
        source="categoria_finalidade", read_only=True
    )

    class Meta:
        model = Finalidade
        fields = fields = [
            "id_finalidade",
            "finalidade",
            "tipo_despesa",
            "categoria_finalidade",
            "tipo_despesa_detail",
            "categoria_finalidade_detail",
            "modalidade",
        ]
        read_only_fields = ["id_finalidade"]


class SubunidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subunidade
        fields = ["id_subunidade", "subunidade", "grupo"]
        read_only_fields = ["id_subunidade"]
