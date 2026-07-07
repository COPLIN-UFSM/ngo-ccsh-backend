from rest_framework import serializers

from entidades.models import Unidade, Cargo, TipoUnidade, Curso, SituacaoUnidade, Servidor


class UnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = ["id_unidade_interna", "nome_unidade", "centro", "tipo_unidade", "situacao_unidade"]
        read_only_fields = ["id_unidade_interna"]


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = "__all__"
        read_only_fields = "__all__"


class TipoUnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidade
        fields = "__all__"
        read_only_fields = "__all__"


class SituacaoUnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituacaoUnidade
        fields = "__all__"
        read_only_fields = "__all__"


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = "__all__"
        read_only_fields = "__all__"


class ServidorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servidor
        fields = "__all__"
        read_only_fields = "__all__"
