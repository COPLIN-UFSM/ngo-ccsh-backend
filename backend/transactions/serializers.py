from calendar import c

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Finalidades


class FinalidadesSerializer(serializers.ModelSerializer):
    class Meta:
        model: Finalidades
        fields = ["finalidade", "id_tipo_despesa"]

