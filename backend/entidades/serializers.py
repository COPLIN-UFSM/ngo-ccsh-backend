from rest_framework import serializers

from entidades.models import Unidade


class UnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = ["id_unidade_interna", "nome_unidade", "centro", "tipo_unidade", "situacao_unidade"]
        read_only_fields = ["id_unidade_interna"]