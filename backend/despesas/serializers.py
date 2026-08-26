from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from despesas.models import *
from entidades.serializers import PessoaSerializer, UnidadeField, PessoaField
from usuarios.serializers import UserDetailsSerializer


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = ["id_tipo_documento", "tipo_documento"]
        read_only_fields = ["id_tipo_documento"]


class ValorDocumentoSerializer(serializers.ModelSerializer):
    tipo_documento = TipoDocumentoSerializer(read_only=True)

    id_tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all(),
        source="tipo_documento",  # Aponta para o atributo do modelo Django
        write_only=True
    )

    class Meta:
        model = ValorDocumento
        fields = ["id_valor_documento", "id_tipo_documento", "tipo_documento", "valor_documento", "transacao",
                  "descricao"]
        read_only_fields = ["id_valor_documento"]


class GrupoFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoFinalidade
        fields = ["id_grupo_finalidade", "grupo_finalidade", "ativo"]
        read_only_fields = ["id_grupo_finalidade"]
        extra_kwargs = {
            "ativo": {"write_only": True},
        }


class NaturezaFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturezaFinalidade
        fields = ["id_natureza_finalidade", "natureza_finalidade", "ativo"]
        read_only_fields = ["id_natureza_finalidade"]
        extra_kwargs = {
            "ativo": {"write_only": True},
        }


class TipoDocumentoField(serializers.RelatedField):

    def to_representation(self, value):
        return TipoDocumentoSerializer(value).data

    def to_internal_value(self, data):
        try:
            if not isinstance(data, int):
                raise ValidationError('O ID do tipo de documento deve ser um número inteiro.')
            return TipoDocumento.objects.get(pk=data)
        except TipoDocumento.DoesNotExist:
            raise ValidationError('Não existe nenhum tipo de documento com este ID.')


class TipoDocumentoParaFinalidadeSerializer(serializers.ModelSerializer):
    tipo_documento = TipoDocumentoField(queryset=TipoDocumento.objects.filter(ativo=True))

    class Meta:
        model = TipoDocumentoParaFinalidade
        fields = ["tipo_documento", "obrigatorio"]

    def validate_tipo_documento(self, value):
        if not value.ativo:
            raise serializers.ValidationError(
                f"O tipo de documento '{value.tipo_documento}' não está ativo."
            )
        return value


class GrupoFinalidadeField(serializers.RelatedField):
    def to_representation(self, value):
        return GrupoFinalidadeSerializer(value).data

    def to_internal_value(self, data):
        try:
            return GrupoFinalidade.objects.get(pk=data)
        except GrupoFinalidade.DoesNotExist:
            raise ValidationError('Não existe nenhum grupo de finalidade com este ID.')


class NaturezaFinalidadeField(serializers.RelatedField):
    def to_representation(self, value):
        return NaturezaFinalidadeSerializer(value).data

    def to_internal_value(self, data):
        try:
            return NaturezaFinalidade.objects.get(pk=data)
        except NaturezaFinalidade.DoesNotExist:
            raise ValidationError('Não existe nenhuma natureza de finalidade com este ID.')


class FinalidadeSerializer(serializers.ModelSerializer):
    natureza_finalidade = NaturezaFinalidadeField(queryset=NaturezaFinalidade.objects.all())
    grupo_finalidade = GrupoFinalidadeField(queryset=GrupoFinalidade.objects.all())

    tipos_documentos = TipoDocumentoParaFinalidadeSerializer(
        source="tipodocumentoparafinalidade_set", many=True)

    class Meta:
        model = Finalidade
        fields = [
            "id_finalidade",
            "natureza_finalidade",
            "grupo_finalidade",
            "finalidade",
            "tipos_documentos"
        ]

        read_only_fields = ["id_finalidade"]

    def validate_tipos_documentos(self, data):
        list_id_tipos_documentos = []
        for tipo_doc in data:
            list_id_tipos_documentos.append(tipo_doc['tipo_documento'])

        if len(list_id_tipos_documentos) > len(set(list_id_tipos_documentos)):
            raise serializers.ValidationError("Os ids de documentos devem ser únicos")
        return data

    def create(self, validated_data):
        tipos_documentos = validated_data.pop("tipodocumentoparafinalidade_set", [])

        with transaction.atomic():
            finalidade = Finalidade.objects.create(**validated_data)
            relations = [
                TipoDocumentoParaFinalidade(
                    finalidade=finalidade,
                    tipo_documento=item['tipo_documento'],
                    obrigatorio=item.get("obrigatorio", True)
                )
                for item in tipos_documentos
            ]

            if len(relations) > 0:
                TipoDocumentoParaFinalidade.objects.bulk_create(relations)

        return finalidade

    def update(self, instance, validated_data):
        tipos_documentos = validated_data.pop("tipodocumentoparafinalidade_set", [])

        instance = super().update(instance, validated_data)

        for item in tipos_documentos:
            item_registered = False
            for tipo_registered in instance.tipodocumentoparafinalidade_set.all():
                if item['tipo_documento'].id_tipo_documento == tipo_registered.tipo_documento.id_tipo_documento:
                    tipo_registered.obrigatorio = item.get('obrigatorio', True)
                    # tipo_registered.ativo = item.get('obrigatorio', tipo_registered.ativo)
                    tipo_registered.save()
                    item_registered = True
                    break
            if not item_registered:
                TipoDocumentoParaFinalidade.objects.create(
                    finalidade=instance,
                    tipo_documento=item['tipo_documento'],
                    obrigatorio=item.get('obrigatorio', True)
                )
        return instance


# OK
class ValorDocumentosNestedSerializer(serializers.ModelSerializer):
    tipo_documento = TipoDocumentoField(queryset=TipoDocumento.objects.all())

    class Meta:
        model = ValorDocumento
        exclude = ["tipo_documento", "valor_documento", "versao_transacao"]
        extra_kwargs = {
            "versao_transacao": {"write_only": True}
        }


class FinalidadeField(serializers.RelatedField):
    def to_representation(self, value):
        return FinalidadeSerializer(value).data

    def to_internal_value(self, data):
        try:
            return Finalidade.objects.get(pk=data)
        except Finalidade.DoesNotExist:
            raise ValidationError('Não existe nenhuma finalidade com este ID.')


class StatusTransacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusTransacao
        fields = "__all__"


class StatusTransacaoField(serializers.RelatedField):
    def to_representation(self, value):
        return StatusTransacaoSerializer(value).data

    def to_internal_value(self, data):
        try:
            return StatusTransacao.objects.get(pk=data)
        except StatusTransacao.DoesNotExist:
            raise ValidationError('Não existe nenhum status com este ID.')

class VersaoTransacaoSerializer(serializers.ModelSerializer):
    documentos = ValorDocumentosNestedSerializer(many=True, required=False, allow_empty=True)

    finalidade = FinalidadeField(required=False, allow_null=True, queryset=Finalidade.objects.all())
    unidade_credora = UnidadeField(required=False, allow_empty=True, queryset=Unidade.objects.all())
    unidade_executora = UnidadeField(required=True, queryset=Unidade.objects.all())
    status_pagamento = StatusTransacaoField(queryset=StatusTransacao.objects.all())
    beneficiario = PessoaField(queryset=Pessoa.objects.all())
    usuario = UserDetailsSerializer(read_only=True)
    # empenho = Empenho

    def validate_documentos(self, documentos):
        if self.finalidade is None:
            return documentos

        tipos_documentos = self.finalidade['tipodocumentoparafinalidade_set'].all()

        validation_errors = []

        for tipo_doc in tipos_documentos:
            if tipo_doc['obrigatorio']:
                if tipo_doc['tipo_documento']['id_tipo_documento'] not in documentos:
                    validation_errors.append(
                        f'O tipo documento {tipo_doc["tipo_documento"]["tipo_documento"]} é obrigatório.')
                    continue

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        tipos_documentos_in_finalidade = [id_doc for id_doc in tipos_documentos['tipo_documento']['id_tipo_documento']]
        for documentos_send in documentos:
            if documentos_send not in tipos_documentos_in_finalidade:
                documentos.pop(documentos_send)

        return documentos

    def create(self, validated_data):
        documentos_data = validated_data.pop("documentos", [])
        transacao = Transacao.objects.create(**validated_data)

        with transaction.atomic():
            docs = [
                ValorDocumento(transacao=transacao, **doc) for doc in documentos_data
            ]
            ValorDocumento.objects.bulk_create(docs)

        return transacao

    class Meta:
        model = Transacao
        fields = [
            "id_transacao",
            "transacao",
            "numero_versao"
            "finalidade",
            "unidade_credora",
            "unidade_executora",
            "usuario",
            "status_pagamento",
            "beneficiario",
            "credito",
            "montante",
            "data_criacao",
            "documentos",
        ]

    # def validate(self, data):
    #     empenho = data.get("empenho")
    #     montante = data.get("montante")
    #     id_transacao = data.get("id_transacao")
    #     eh_credito = data.get("eh_credito")
    #
    #     if empenho and not empenho.ativo:
    #         raise serializers.ValidationError(
    #             {"empenho": "Não é possível criar ou modificar transações de um empenho inativo."}
    #         )
    #
    #     queryset = Transacao.objects.filter(empenho=empenho)
    #     if self.instance:
    #         queryset = queryset.exclude(id_transacao=id_transacao)
    #
    #     total_despesas = (
    #             queryset.aggregate(
    #                 total=Sum(
    #                     Case(
    #                         When(eh_credito=True, then=F("montante")),
    #                         When(eh_credito=False, then=-F("montante")),
    #                     )
    #                 )
    #             )["total"]
    #             or 0.00
    #     )
    #
    #     if not eh_credito and montante > total_despesas:
    #         raise serializers.ValidationError(
    #             {
    #                 "montante": f"Saldo insuficiente. O Valor da despesa (R$ {montante:.2f}) é maior que o saldo atual (R$ {total_despesas:.2f})."}
    #         )
    #     return data


# OK
class TransacaoSerializer(serializers.ModelSerializer):
    versao_transacao = VersaoTransacaoSerializer()

    class Meta:
        model = Transacao
        fields = ['id_transacao', 'versao_transacao', 'data_criacao']
        read_only_fields = ['id_transacao', 'data_criacao']


















    # class EmpenhoSerializer(serializers.ModelSerializer):
    #     transacoes = TransacaoSerializer(many=True, read_only=True)
    #     montante = serializers.SerializerMethodField()
    #
    #     class Meta:
    #         model = Empenho
    #         fields = ["id_empenho", "numero_empenho", "numero_pen", "descricao", "finalidade", "montante", "transacoes"]
    #         read_only_fields = ["id_empenho"]
    #
    #     def get_montante(self, obj):
    #         valor_somado = (
    #                 Transacao.objects.filter(empenho=obj).aggregate(
    #                     total=Sum(
    #                         Case(
    #                             When(eh_credito=True, then=F("montante")),
    #                             When(eh_credito=False, then=-F("montante")),
    #                         )
    #                     )
    #                 )["total"]
    #                 or 0.00
    #         )
    #
    #         return valor_somado
    #
    # class StatusTransacaoSerializer(serializers.ModelSerializer):
    #     class Meta:
    #         model = StatusTransacao
    #         fields = "__all__"
