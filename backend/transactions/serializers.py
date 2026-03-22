from ast import Raise
from calendar import c
from os import error

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *


class FinalidadesSerializer(serializers.ModelSerializer):
    tipo_despesa = serializers.PrimaryKeyRelatedField(
        queryset=TipoDespesa.objects.all(),
        error_messages={
            "does_not_exist": "Código de despesa inexistente.",
            "incorrect_type": "Formato de dado inválido para o tipo de despesa.",
        },
    )
    subtipo_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=SubtipoFinalidades.objects.all(),
        error_messages={
            "does_not_exist": "Código de subtipo da finalidade inexistente.",
            "incorrect_type": "Formato de dado inválido para o subtipo da finalidade.",
        },
    )

    class Meta:
        model = Finalidades
        fields = ["finalidade", "tipo_despesa", "subtipo_finalidade"]


class SubtipoFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubtipoFinalidades
        fields = ["id_subtipo_finalidade","subtipo_finalidade"]
        read_only_fields = ["id_subtipo_finalidade"]
