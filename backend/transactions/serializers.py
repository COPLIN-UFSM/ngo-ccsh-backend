from rest_framework import serializers
from .models import *


class CategoriaFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaFinalidade
        fields = ["id_subtipo_finalidade", "subtipo_finalidade"]
        read_only_fields = ["id_subtipo_finalidade"]


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

    subtipo_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaFinalidade.objects.all(),
        write_only=True,
        error_messages={
            "does_not_exist": "Código de subtipo da finalidade inexistente.",
            "incorrect_type": "Formato de dado inválido para o subtipo da finalidade.",
        },
    )

    tipo_despesa_detail = TipoDespesaSerializer(source="tipo_despesa", read_only=True)
    subtipo_finalidade_detail = CategoriaFinalidadeSerializer(
        source="subtipo_finalidade", read_only=True
    )

    class Meta:
        model = Finalidade
        fields = fields = [
            "id_finalidade",
            "finalidade",
            "tipo_despesa",
            "subtipo_finalidade",
            "tipo_despesa_detail",
            "subtipo_finalidade_detail",
        ]
        read_only_fields = ["id_finalidade"]
