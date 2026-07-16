from rest_framework import serializers

from entidades.models import Unidade, Cargo, TipoUnidade, Curso, SituacaoUnidade, Servidor, Discente, Centro, Pessoa, \
    Email, Telefone


class CentroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centro
        fields = ["id_centro_interno", "nome_centro", "sigla_centro", "cod_estruturado"]

    # def validate(self, attrs):

class SituacaoUnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituacaoUnidade
        fields = "__all__"
        extra_kwargs = {field.name: {'read_only': True} for field in SituacaoUnidade._meta.fields}


class TipoUnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidade
        fields = "__all__"
        extra_kwargs = {field.name: {'read_only': True} for field in TipoUnidade._meta.fields}


class UnidadeSerializer(serializers.ModelSerializer):
    tipo_unidade = TipoUnidadeSerializer()
    situacao_unidade = SituacaoUnidadeSerializer()
    centro = CentroSerializer()

    class Meta:
        model = Unidade
        fields = ["id_unidade_interna", "nome_unidade", "cod_estruturado", "centro", "tipo_unidade", "situacao_unidade"]
        extra_kwargs = {field.name: {'read_only': True} for field in Unidade._meta.fields}


class CursoSerializer(serializers.ModelSerializer):
    centro = serializers.StringRelatedField()
    class Meta:
        model = Curso
        fields = "__all__"
        extra_kwargs = {field.name: {'read_only': True} for field in Curso._meta.fields}

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = "__all__"
        extra_kwargs = {field.name: {'read_only': True} for field in Cargo._meta.fields}


class PessoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pessoa
        fields = ["id_pessoa_interna", "nome_pessoa", "cpf", "rg"]
        read_only_fields = ["rg", "cpf"]


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = "__all__"

class DiscenteSerializer(serializers.ModelSerializer):
    email = EmailSerializer()
    curso = CursoSerializer()

    class Meta:
        model = Discente
        fields = "__all__"
        extra_kwargs = {field.name: {'read_only': True} for field in Discente._meta.fields}


class ServidorSerializer(serializers.ModelSerializer):
    email = EmailSerializer()
    curso = CursoSerializer()
    cargo = CargoSerializer()

    class Meta:
        model = Servidor
        fields = "__all__"
        extra_kwargs = {field.name: {'read_only': True} for field in Servidor._meta.fields}




class TelefoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telefone
        fields = "__all__"