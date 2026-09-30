from django.db import transaction
from django.forms.models import model_to_dict
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from despesas.models import *


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = ["id_tipo_documento", "tipo_documento", "ativo"]
        read_only_fields = ["id_tipo_documento"]


class ValorDocumentoSerializer(serializers.ModelSerializer):
    id_tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all(),
        source="tipo_documento",
    )
    tipo_documento = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ValorDocumento
        fields = ["id_tipo_documento", "valor_documento", "tipo_documento"]

    def create(self, validated_data):
        view = self.context.get("view")
        if not view:
            raise serializers.ValidationError("O id da transação deve ser enviado via URL.")

        id_transacao = view.kwargs.get("transacao_pk")
        try:
            transacao = Transacao.objects.get(pk=id_transacao)
        except Transacao.DoesNotExist:
            raise serializers.ValidationError("Transação não encontrada.")
        validated_data['versao_transacao'] = transacao.versao_transacao
        transacao = ValorDocumento.objects.create(**validated_data)
        return transacao


class GrupoFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoFinalidade
        fields = ["id_grupo_finalidade", "grupo_finalidade", "ativo"]
        read_only_fields = ["id_grupo_finalidade"]


class NaturezaFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturezaFinalidade
        fields = ["id_natureza_finalidade", "natureza_finalidade", "ativo"]
        read_only_fields = ["id_natureza_finalidade"]


class TipoDocumentoParaFinalidadeSerializer(serializers.ModelSerializer):
    tipo_documento = serializers.StringRelatedField(read_only=True)
    id_tipo_documento = PrimaryKeyRelatedField(queryset=TipoDocumento.objects.all(), source="tipo_documento")

    class Meta:
        model = TipoDocumentoParaFinalidade
        fields = ["id_tipo_documento", "tipo_documento", "obrigatorio"]

    def validate_id_tipo_documento(self, value):
        if not value.ativo:
            raise serializers.ValidationError(
                f"O tipo de documento '{value}' não está ativo(a)."
            )
        return value


class FinalidadeSerializer(serializers.ModelSerializer):
    id_natureza_finalidade = PrimaryKeyRelatedField(queryset=NaturezaFinalidade.objects.all(), write_only=True,
                                                    source="natureza_finalidade")
    id_grupo_finalidade = PrimaryKeyRelatedField(queryset=GrupoFinalidade.objects.all(), write_only=True,
                                                 source="grupo_finalidade")
    natureza_finalidade = serializers.StringRelatedField(read_only=True)
    grupo_finalidade = serializers.StringRelatedField(read_only=True)

    tipos_documentos = TipoDocumentoParaFinalidadeSerializer(
        source="tipodocumentoparafinalidade_set", many=True)

    class Meta:
        model = Finalidade
        fields = [
            "id_finalidade",
            "natureza_finalidade",
            "grupo_finalidade",
            "id_natureza_finalidade",
            "id_grupo_finalidade",
            "finalidade",
            "tipos_documentos",
            "ativo"
        ]

        read_only_fields = ["id_finalidade"]

    def validate_id_natureza_finalidade(self, natureza):
        if not natureza.ativo:
            raise serializers.ValidationError(f"A natureza de finalidade '{natureza}' não está ativo(a).")
        return natureza

    def validate_id_grupo_finalidade(self, grupo):
        if not grupo.ativo:
            raise serializers.ValidationError(f"A natureza de finalidade '{grupo}' não está ativo(a).")
        return grupo

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

        tipos_documentos = [i for i in tipos_documentos if 'tipo_documento' in i]

        for item in tipos_documentos:
            item_registered = False
            for tipo_registered in instance.tipodocumentoparafinalidade_set.all():
                if item['tipo_documento'].pk == tipo_registered.tipo_documento.id_tipo_documento:
                    tipo_registered.obrigatorio = item.get('obrigatorio', True)
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
    tipo_documento = TipoDocumentoSerializer(read_only=True)
    id_documento = PrimaryKeyRelatedField(queryset=TipoDocumento.objects.all(), source="tipo_documento")

    class Meta:
        model = ValorDocumento
        exclude = ["id_tipo_documento", "tipo_documento", "valor_documento", "versao_transacao"]
        extra_kwargs = {
            "versao_transacao": {"write_only": True}
        }


class StatusTransacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusTransacao
        fields = "__all__"


class TransacaoReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transacao
        fields = ['id_transacao', 'data_criacao']
        read_only_fields = ['id_transacao', 'data_criacao']


class VersaoTransacaoSerializer(serializers.ModelSerializer):
    id_finalidade = PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Finalidade.objects.all(),
                                           source="finalidade")
    id_unidade_credora = serializers.PrimaryKeyRelatedField(queryset=Unidade.objects.all(), required=False,
                                                            allow_null=True, source="unidade_credora")
    id_unidade_executora = serializers.PrimaryKeyRelatedField(queryset=Unidade.objects.all(),
                                                              source="unidade_executora")
    id_status_pagamento = serializers.PrimaryKeyRelatedField(queryset=StatusTransacao.objects.all(),
                                                             source="status_pagamento")
    id_beneficiario = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Pessoa.objects.all(),
                                                         source="beneficiario")
    id_usuario = serializers.PrimaryKeyRelatedField(read_only=True, source="usuario")

    finalidade = serializers.StringRelatedField(read_only=True)
    unidade_credora = serializers.StringRelatedField(read_only=True)
    unidade_executora = serializers.StringRelatedField(read_only=True)
    status_pagamento = serializers.StringRelatedField(read_only=True)
    beneficiario = serializers.StringRelatedField(read_only=True)
    id_transacao = serializers.PrimaryKeyRelatedField(queryset=Transacao.objects.all(), source="transacao")

    documentos = ValorDocumentoSerializer(many=True, required=False)

    class Meta:
        model = VersaoTransacao
        fields = [
            "id_versao_transacao",
            "id_transacao",
            "numero_versao",
            "id_finalidade",
            "finalidade",
            "id_unidade_credora",
            "unidade_credora",
            "id_unidade_executora",
            "unidade_executora",
            "id_usuario",
            "id_status_pagamento",
            "status_pagamento",
            "id_beneficiario",
            "beneficiario",
            "documentos",
            "credito",
            "montante",
            "data_criacao"
        ]

    def validate(self, data):
        finalidade = data.get('finalidade')
        documentos = data.get('documentos', [])
        documentos_id = [doc['tipo_documento'].pk for doc in documentos]

        validation_errors = []
        vistos = set()
        for doc in documentos_id:
            if doc not in vistos:
                vistos.add(doc)
            else:
                validation_errors.append({
                    "id_tipo_documento": doc,
                    "error": "Não é possível enviar mais de um documento do mesmo tipo."
                })

        if not finalidade:
            if validation_errors:
                raise serializers.ValidationError({'documentos': validation_errors})
            return data

        tipos_documentos_possiveis = finalidade.tipodocumentoparafinalidade_set.select_related('tipo_documento').all()
        tipos_documentos_possiveis_pk = [tipo_doc.tipo_documento.pk for tipo_doc in tipos_documentos_possiveis]

        for tipo_doc in tipos_documentos_possiveis:
            if tipo_doc.obrigatorio and tipo_doc.tipo_documento.pk not in documentos_id:
                validation_errors.append({
                    "id_tipo_documento": tipo_doc.tipo_documento.pk,
                    "error": f"O tipo documento '{tipo_doc.tipo_documento.tipo_documento}' é obrigatório para esta finalidade."
                })

        for doc in documentos:
            tipo_doc_obj = doc['tipo_documento']
            if tipo_doc_obj.pk not in tipos_documentos_possiveis_pk:
                validation_errors.append({
                    "id_tipo_documento": tipo_doc_obj.pk,
                    "error": f"O tipo de documento '{tipo_doc_obj.tipo_documento}' não é permitido para esta finalidade."
                })

        if validation_errors:
            raise serializers.ValidationError({'documentos': validation_errors})

        return data

    def create(self, validated_data):
        documentos_data = validated_data.pop("documentos", [])
        user = self.context['request'].user

        versao_transacao = None
        with transaction.atomic():
            versao_transacao = VersaoTransacao.objects.create(**validated_data, usuario=user)
            docs = [
                ValorDocumento(versao_transacao=versao_transacao, **doc) for doc in documentos_data
            ]
            ValorDocumento.objects.bulk_create(docs)

        return versao_transacao

        # def update(self, instance, validated_data):
        #     documentos_data = validated_data.pop("documentos", [])
        #     user = self.context['request'].user
        #     validated_data['numero_versao'] = int(instance.numero_versao) + 1
        #     old_versao_transacao = model_to_dict(instance.versao_transacao, exclude=['id_versao_transacao'])
        #
        #     new_data = validated_data.pop('transacao', None)
        #     if new_data is not None:
        #         raise serializers.ValidationError({'transacao': 'Nenhum campo foi atualizado.'})
        #
        #     new_versao_transacao = {**old_versao_transacao, **new_data}
        #     raise serializers.ValidationError(new_versao_transacao)

        versao_transacao = VersaoTransacao.objects.create(**validated_data, usuario=user)
        # versao_transacao = None
        # with transaction.atomic():
        # docs = [
        #     ValorDocumento(versao_transacao=versao_transacao, **doc) for doc in documentos_data
        # ]
        # ValorDocumento.objects.bulk_create(docs)

        return versao_transacao

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


class TransacaoSerializer(serializers.ModelSerializer):
    transacao = VersaoTransacaoSerializer(read_only=True, allow_null=False, source="versao_transacao")

    class Meta:
        model = Transacao
        fields = ['id_transacao', 'transacao', 'data_criacao']
        read_only_fields = ['id_transacao', 'data_criacao']

    def create(self, validated_data):
        versao_transacao_data = self.initial_data.get('transacao', None)

        with transaction.atomic():
            transacao = Transacao.objects.create(**validated_data)
            if versao_transacao_data is not None:
                versao_transacao_data['id_transacao'] = transacao.pk
                versao_transacao_data['numero_versao'] = 1
                versao_serializer = VersaoTransacaoSerializer(data=versao_transacao_data, context=self.context)
                versao_serializer.is_valid(raise_exception=True)
                versao_transacao = versao_serializer.save()
                transacao.versao_transacao = versao_transacao
                transacao.save()

        return transacao

    def update(self, instance, validated_data):

        versao_transacao_data = self.initial_data.get('transacao', None)
        if versao_transacao_data is None:
            raise serializers.ValidationError('Nenhum dado foi atualizado')

        old_docs = [{
            "id_tipo_documento": doc.tipo_documento.pk,
            "valor_documento": doc.valor_documento,
        } for doc in ValorDocumento.objects.filter(versao_transacao=instance.versao_transacao)]

        id_finalidade = versao_transacao_data.pop('id_finalidade', None)
        if id_finalidade and instance.versao_transacao.finalidade.pk != id_finalidade:
            tipos_docs = TipoDocumentoParaFinalidade.objects.filter(finalidade=id_finalidade)
            tipos_docs_id = [doc.tipo_documento.pk for doc in tipos_docs]

            for doc in old_docs.copy():
                if doc['id_tipo_documento'] not in tipos_docs_id:
                    old_docs.remove(doc)

        old_versao_transacao = model_to_dict(instance.versao_transacao, exclude=['id_versao_transacao'])
        for field, value in old_versao_transacao.copy().items():
            if field in ['transacao', 'finalidade', 'unidade_executora', 'unidade_credora', 'usuario',
                         'status_pagamento', 'empenho', 'beneficiario']:
                old_versao_transacao.pop(field)
                old_versao_transacao[f'id_{field}'] = value

        new_docs = versao_transacao_data.pop('documentos', [])

        if old_docs or new_docs:
            dados_combinados = {doc['id_tipo_documento']: doc for doc in old_docs}
            dados_combinados.update({doc['id_tipo_documento']: doc for doc in new_docs})
            old_versao_transacao['documentos'] = list(dados_combinados.values())


        new_data = {**old_versao_transacao, **versao_transacao_data}
        for field, value in new_data.copy().items():
            if value is None:
                new_data.pop(field)

        with transaction.atomic():
            new_data['numero_versao'] = int(instance.versao_transacao.numero_versao) + 1
            new_data['id_transacao'] = instance.pk
            versao_serializer = VersaoTransacaoSerializer(data=new_data, context=self.context)
            versao_serializer.is_valid(raise_exception=True)

            versao_transacao = versao_serializer.save()
            instance.versao_transacao = versao_transacao
            instance.save()
        return instance

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
