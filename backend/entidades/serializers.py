from django.core.exceptions import ValidationError
from django.db.models import Model
from rest_framework import serializers

from entidades.models import Unidade, Cargo, TipoUnidade, Curso, SituacaoUnidade, Servidor, Discente, Centro, Pessoa, \
    Email, Telefone, PessoaSIE


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


# class TipoUnidadeField(serializers.RelatedField):
#     def to_representation(self, value: TipoUnidade):
#         return value.tipo_unidade
#
#     def to_internal_value(self, data: TipoUnidade):
#         try:
#             return TipoUnidade.objects.get(id_tipo_unidade=data).pk
#         except TipoUnidade.DoesNotExist:
#             raise ValidationError('não existe nenhum tipo de unidade com este ID.')
#
# class SituacaoUnidadeField(serializers.RelatedField):
#     def to_representation(self, value: SituacaoUnidade):
#         return value.situacao_unidade
#
#     def to_internal_value(self, data: SituacaoUnidade):
#         try:
#             return SituacaoUnidade.objects.get(id_situacao_unidade=data).pk
#         except SituacaoUnidade.DoesNotExist:
#             raise ValidationError('Não existe nenhuma situacao de unidade com este ID.')

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
            return Centro._base_manager.get(id_centro_interno=data).pk
        except Centro.DoesNotExist:
            raise ValidationError('Não existe nenhum centro com este ID.')


# OK
class UnidadeSerializer(serializers.ModelSerializer):
    id_tipo_unidade = serializers.PrimaryKeyRelatedField(queryset=TipoUnidade.objects.all(), source="tipo_unidade")
    id_situacao_unidade = serializers.PrimaryKeyRelatedField(queryset=SituacaoUnidade.objects.all(),
                                                             source="situacao_unidade")
    id_centro = serializers.PrimaryKeyRelatedField(queryset=Centro.objects.all(), source="centro")

    tipo_unidade = serializers.StringRelatedField(read_only=True)
    situacao_unidade = serializers.StringRelatedField(read_only=True)
    centro = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Unidade
        fields = ["id_unidade_interna", "nome_unidade", "cod_estruturado", "id_centro", "centro", "id_tipo_unidade",
                  "tipo_unidade", "id_situacao_unidade", "situacao_unidade"]
        read_only = ['id_unidade_interna']


class UnidadeField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value: Centro):
        return UnidadeSerializer(value).data


class CursoSerializer(serializers.ModelSerializer):
    id_centro = serializers.PrimaryKeyRelatedField(queryset=Centro.objects.all(), source="centro")
    nome_centro = serializers.CharField(source="centro.nome_centro", read_only=True)
    sigla_centro = serializers.CharField(source="centro.sigla_centro", read_only=True)

    class Meta:
        model = Curso
        fields = ['id_curso', "id_centro", "nome_centro", "sigla_centro", "nome_curso", "nivel_curso",
                  "modalidade_curso", "classificacao_curso"]


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = "__all__"
        extra_kwargs = {field.name: {'read_only': True} for field in Cargo._meta.fields}


class TelefoneSerializer(serializers.ModelSerializer):
    id_pessoa_interna = serializers.PrimaryKeyRelatedField(queryset=Pessoa.objects.all(), source="pessoa")
    nome_pessoa = serializers.CharField(source="pessoa.nome_pessoa", read_only=True)

    class Meta:
        model = Telefone
        fields = ["id_telefone", "id_pessoa_interna", "nome_pessoa", "telefone"]


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = "__all__"


class TelefonePessoaSerializer(serializers.ModelSerializer):
    id_telefone = serializers.IntegerField(required=False)

    class Meta:
        model = Telefone
        fields = ['id_telefone', 'telefone']


class EmailPessoaSerializer(serializers.ModelSerializer):
    id_email = serializers.IntegerField(required=False)

    class Meta:
        model = Email
        fields = ['id_email', 'email']


class PessoaSerializer(serializers.ModelSerializer):
    telefones = TelefonePessoaSerializer(many=True, source="telefone_set", required=False)
    emails = EmailPessoaSerializer(many=True, source="email_set", required=False)

    class Meta:
        model = Pessoa
        fields = ["id_pessoa_interna", "nome_pessoa", "cpf", "rg", "telefones", "emails"]
        read_only_fields = ["id_pessoa_interna"]

    def validate_cpf(self, value):
        try:
            Pessoa.objects.get(cpf=value)
            raise serializers.ValidationError(f"Já existe uma pessoa com o CPF {value}.")
        except Pessoa.DoesNotExist:
            return value

    def create(self, validated_data):
        telefones_data = validated_data.pop("telefone_set", [])
        emails_data = validated_data.pop("email_set", [])

        pessoa = Pessoa.objects.create(**validated_data)

        for telefone in telefones_data:
            Telefone.objects.create(pessoa=pessoa, **telefone)

        for email in emails_data:
            Email.objects.create(pessoa=pessoa, **email)

        return pessoa

    def update(self, instance: Pessoa, validated_data):
        telefones_data = validated_data.pop("telefone_set", [])
        emails_data = validated_data.pop("email_set", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        fields_errors = {
            "telefones": [],
            "emails": []
        }
        for telefone in telefones_data:
            telefone_id = telefone.pop("id_telefone", None)

            if telefone_id:
                telefone = Telefone.objects.filter(pk=telefone_id, pessoa=instance).update(**telefone, pessoa=instance)
                if not telefone:
                    fields_errors['telefones'].append(
                        f"Telefone com ID {telefone_id} não encontrado para a pessoa {instance.nome_pessoa}")
            else:
                Telefone.objects.create(pessoa=instance, **telefone)

        for email in emails_data:
            email_id = email.pop("id_email", None)

            if email_id:
                email = Email.objects.filter(pk=email_id, pessoa=instance).update(**email, pessoa=instance)
                if not email:
                    fields_errors['emails'].append(
                        f"Email com ID {email_id} não encontrado para a pessoa {instance.nome_pessoa}")

            else:
                Email.objects.create(pessoa=instance, **email)

        if fields_errors['telefones'] or fields_errors['emails']:
            raise serializers.ValidationError(fields_errors)

        instance.refresh_from_db()
        return instance


class PessoaField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, data):
        return PessoaSerializer(data).data


class DiscenteSerializer(serializers.ModelSerializer):
    id_pessoa_interna = serializers.PrimaryKeyRelatedField(source="pessoa", read_only=True)
    nome_pessoa = serializers.CharField(source="pessoa.nome_pessoa", read_only=True)
    cpf = serializers.CharField(source="pessoa.cpf", read_only=True)
    rg = serializers.CharField(source="pessoa.rg", read_only=True)

    id_curso = serializers.PrimaryKeyRelatedField(source="curso", read_only=True)
    id_centro = serializers.PrimaryKeyRelatedField(source="curso.centro", read_only=True)
    nome_centro = serializers.CharField(source="curso.centro.nome_centro", read_only=True)
    sigla_centro = serializers.CharField(source="curso.centro.sigla_centro", read_only=True)
    nome_curso = serializers.CharField(source="curso.nome_curso", read_only=True)
    nivel_curso = serializers.CharField(source="curso.nivel_curso", read_only=True)
    modalidade_curso = serializers.CharField(source="curso.modalidade_curso", read_only=True)
    classificacao_curso = serializers.CharField(source="curso.classificacao_curso", read_only=True)

    telefones = serializers.SerializerMethodField()
    emails = serializers.SerializerMethodField()

    class Meta:
        model = Discente
        fields = [
            "id_curso_aluno",
            "id_pessoa_interna",
            "nome_pessoa",
            "cpf", "rg", "id_curso", "id_centro", "nome_centro", "sigla_centro", "nome_curso", "nivel_curso",
            "modalidade_curso",
            "classificacao_curso", "matricula", "telefones", "emails", "ativo"
        ]

    def get_telefones(self, obj):
        if obj.pessoa:
            queryset = obj.pessoa.telefone_set.all()
            return TelefonePessoaSerializer(queryset, many=True, context=self.context).data
        return []

    def get_emails(self, obj):
        if obj.pessoa:
            queryset = obj.pessoa.email_set.all()
            return EmailPessoaSerializer(queryset, many=True, context=self.context).data
        return []


class ServidorSerializer(serializers.ModelSerializer):
    id_pessoa_interna = serializers.PrimaryKeyRelatedField(queryset=Pessoa.objects.all(), source="pessoa")
    nome_pessoa = serializers.CharField(source="pessoa.nome_pessoa", read_only=True)
    cpf = serializers.CharField(source="pessoa.cpf", read_only=True)
    rg = serializers.CharField(source="pessoa.rg", read_only=True)

    cargo = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Servidor
        fields = ["id_contrato_rh", "id_pessoa_interna", "nome_pessoa", "cpf", "rg", "cargo", "matricula",
                  "telefones", "emails", "ativo"]

    telefones = serializers.SerializerMethodField()
    emails = serializers.SerializerMethodField()

    def get_telefones(self, obj):
        if obj.pessoa:
            queryset = obj.pessoa.telefone_set.all()
            return TelefonePessoaSerializer(queryset, many=True, context=self.context).data
        return []

    def get_emails(self, obj):
        if obj.pessoa:
            queryset = obj.pessoa.email_set.all()
            return EmailPessoaSerializer(queryset, many=True, context=self.context).data
        return []
