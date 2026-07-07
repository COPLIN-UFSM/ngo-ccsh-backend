from rest_framework import serializers

from entidades.models import Unidade, Cargo, TipoUnidade, Curso, SituacaoUnidade, Servidor, Discente, Centro, Pessoa, \
    Email, Telefone


class CentroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centro
        fields = ["id_centro_interno", "nome_centro", "sigla_centro", "cod_estruturado"]
        read_only_fields = "__all__"


class SituacaoUnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituacaoUnidade
        fields = "__all__"
        read_only_fields = "__all__"


class TipoUnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidade
        fields = "__all__"
        read_only_fields = "__all__"


class UnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = ["id_unidade_interna", "nome_unidade", "cod_estruturado", "centro", "tipo_unidade", "situacao_unidade"]
        read_only_fields = "__all__"


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = "__all__"
        read_only_fields = "__all__"


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = "__all__"
        read_only_fields = "__all__"


class PessoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pessoa
        fields = ["id_pessoa_interna", "nome_pessoa", "cpf", "rg"]
        read_only_fields = ["rg", "cpf"]


class DiscenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discente
        fields = "__all__"
        read_only_fields = "__all__"


class ServidorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servidor
        fields = "__all__"
        read_only_fields = "__all__"


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = "__all__"


class TelefoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telefone
        fields = "__all__"