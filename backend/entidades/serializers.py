from django.core.exceptions import ValidationError
from rest_framework import serializers

from entidades.models import Unidade, Cargo, TipoUnidade, Curso, SituacaoUnidade, Servidor, Discente, Centro, Pessoa, \
    Email, Telefone


class CentroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centro
        fields = ["id_centro_interno", "nome_centro", "sigla_centro", "cod_estruturado"]
        read_only = ["id_centro_interno"]

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

class TipoUnidadeField(serializers.RelatedField):
    def to_representation(self, value: TipoUnidade):
        return value.tipo_unidade

    def to_internal_value(self, data: TipoUnidade):
        try:
            return TipoUnidade.objects.get(id_tipo_unidade=data)
        except TipoUnidade.DoesNotExist:
            raise ValidationError('não existe nenhum tipo de unidade com este ID.')

class SituacaoUnidadeField(serializers.RelatedField):
    def to_representation(self, value: SituacaoUnidade):
        return value.situacao_unidade

    def to_internal_value(self, data: SituacaoUnidade):
        try:
            return SituacaoUnidade.objects.get(id_situacao_unidade=data)
        except SituacaoUnidade.DoesNotExist:
            raise ValidationError('Não existe nenhuma situacao de unidade com este ID.')

class CentroResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centro
        fields = ["nome_centro", "sigla_centro"]
        read_only = ["nome_centro", "sigla_centro"]

class CentroField(serializers.RelatedField):
    def to_representation(self, value: Centro):
        return CentroResumoSerializer(value).data

    def to_internal_value(self, data: SituacaoUnidade):
        try:
            return Centro._base_manager.get(id_centro_interno=data)
        except Centro.DoesNotExist:
            raise ValidationError('Não existe nenhum centro com este ID.')

#POST e PATCH com problema, GET OK
class UnidadeSerializer(serializers.ModelSerializer):
    tipo_unidade = TipoUnidadeField(queryset=TipoUnidade.objects.all())
    situacao_unidade = SituacaoUnidadeField(queryset=SituacaoUnidade.objects.all())
    centro = CentroField(queryset=Centro.objects.all())

    class Meta:
        model = Unidade
        fields = ["id_unidade_interna", "nome_unidade", "cod_estruturado", "centro", "tipo_unidade", "situacao_unidade"]
        read_only = ['id_unidade_interna']

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