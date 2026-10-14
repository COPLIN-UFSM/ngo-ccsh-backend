from django.db import transaction
from django.forms.models import model_to_dict
from entidades.models import Pessoa, Unidade
from ngo_ccsh.constrains import CAPITAL, CUSTEIO, TRANSFERENCIA_FINALIDADES
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from despesas.models import *
from despesas.models import Empenho, Finalidade


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
            raise serializers.ValidationError(
                "O id da transação deve ser enviado via URL."
            )

        id_transacao = view.kwargs.get("transacao_pk")
        try:
            transacao = Transacao.objects.get(pk=id_transacao)
        except Transacao.DoesNotExist:
            raise serializers.ValidationError("Transação não encontrada.")
        validated_data["versao_transacao"] = transacao.versao_transacao
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
    id_tipo_documento = PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all(), source="tipo_documento"
    )

    class Meta:
        model = TipoDocumentoParaFinalidade
        fields = ["id_tipo_documento", "tipo_documento", "obrigatorio", "ativo"]

    def validate_id_tipo_documento(self, value):
        if not value.ativo:
            raise serializers.ValidationError(
                f"O tipo de documento '{value}' não está ativo(a)."
            )
        return value


class FinalidadeSerializer(serializers.ModelSerializer):
    id_natureza_finalidade = PrimaryKeyRelatedField(
        queryset=NaturezaFinalidade.objects.all(), source="natureza_finalidade"
    )
    id_grupo_finalidade = PrimaryKeyRelatedField(
        queryset=GrupoFinalidade.objects.all(), source="grupo_finalidade"
    )
    natureza_finalidade = serializers.StringRelatedField(read_only=True)
    grupo_finalidade = serializers.StringRelatedField(read_only=True)

    tipos_documentos = TipoDocumentoParaFinalidadeSerializer(
        source="tipodocumentoparafinalidade_set", many=True
    )

    class Meta:
        model = Finalidade
        fields = [
            "id_finalidade",
            "id_natureza_finalidade",
            "natureza_finalidade",
            "grupo_finalidade",
            "id_grupo_finalidade",
            "finalidade",
            "tipos_documentos",
            "ativo",
        ]

        read_only_fields = ["id_finalidade"]

    def validate_id_natureza_finalidade(self, natureza):
        if not natureza.ativo:
            raise serializers.ValidationError(
                f"A natureza de finalidade '{natureza}' não está ativo(a)."
            )
        return natureza

    def validate_id_grupo_finalidade(self, grupo):
        if not grupo.ativo:
            raise serializers.ValidationError(
                f"A natureza de finalidade '{grupo}' não está ativo(a)."
            )
        return grupo

    def create(self, validated_data):
        tipos_documentos = validated_data.pop("tipodocumentoparafinalidade_set", [])
        with transaction.atomic():
            finalidade = Finalidade.objects.create(**validated_data)
            relations = [
                TipoDocumentoParaFinalidade(
                    finalidade=finalidade,
                    tipo_documento=item["tipo_documento"],
                    obrigatorio=item.get("obrigatorio", True),
                )
                for item in tipos_documentos
            ]

            if len(relations) > 0:
                TipoDocumentoParaFinalidade.objects.bulk_create(relations)

        return finalidade

    def update(self, instance, validated_data):
        tipos_documentos = validated_data.pop("tipodocumentoparafinalidade_set", [])
        instance = super().update(instance, validated_data)

        tipos_documentos = [i for i in tipos_documentos if "tipo_documento" in i]

        for item in tipos_documentos:
            item_registered = False
            for tipo_registered in instance.tipodocumentoparafinalidade_set.all():
                if (
                    item["tipo_documento"].pk
                    == tipo_registered.tipo_documento.id_tipo_documento
                ):
                    tipo_registered.obrigatorio = item.get("obrigatorio", True)
                    tipo_registered.ativo = item.get("ativo", instance.ativo)
                    tipo_registered.save()
                    item_registered = True
                    break
            if not item_registered:
                TipoDocumentoParaFinalidade.objects.create(
                    finalidade=instance,
                    tipo_documento=item["tipo_documento"],
                    obrigatorio=item.get("obrigatorio", True),
                )
        return instance


# OK
class ValorDocumentosNestedSerializer(serializers.ModelSerializer):
    tipo_documento = TipoDocumentoSerializer(read_only=True)
    id_documento = PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all(), source="tipo_documento"
    )

    class Meta:
        model = ValorDocumento
        exclude = [
            "id_tipo_documento",
            "tipo_documento",
            "valor_documento",
            "versao_transacao",
        ]
        extra_kwargs = {"versao_transacao": {"write_only": True}}


class StatusTransacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusTransacao
        fields = "__all__"


class TransacaoReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transacao
        fields = ["id_transacao", "data_criacao"]
        read_only_fields = ["id_transacao", "data_criacao"]


class VersaoTransacaoSerializer(serializers.ModelSerializer):
    id_finalidade = PrimaryKeyRelatedField(
        queryset=Finalidade.objects.all(), source="finalidade"
    )
    id_unidade_receptora = serializers.PrimaryKeyRelatedField(
        queryset=Unidade.objects.all(),
        required=False,
        allow_null=True,
        source="unidade_receptora",
    )
    id_unidade_executora = serializers.PrimaryKeyRelatedField(
        queryset=Unidade.objects.all(), source="unidade_executora"
    )
    id_status_pagamento = serializers.PrimaryKeyRelatedField(
        queryset=StatusTransacao.objects.all(), source="status_pagamento"
    )
    id_beneficiario = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=Pessoa.objects.all(),
        source="beneficiario",
    )
    id_usuario = serializers.PrimaryKeyRelatedField(read_only=True, source="usuario")
    id_empenho = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=Empenho.objects.all(),
        source="empenho",
    )

    finalidade = serializers.StringRelatedField(read_only=True)
    unidade_receptora = serializers.StringRelatedField(read_only=True)
    unidade_executora = serializers.StringRelatedField(read_only=True)
    status_pagamento = serializers.StringRelatedField(read_only=True)
    beneficiario = serializers.StringRelatedField(read_only=True)
    empenho = serializers.StringRelatedField(read_only=True)
    id_transacao = serializers.PrimaryKeyRelatedField(
        queryset=Transacao.objects.all(), source="transacao"
    )

    documentos = ValorDocumentoSerializer(many=True, required=False)

    class Meta:
        model = VersaoTransacao
        fields = [
            "id_versao_transacao",
            "id_transacao",
            "numero_versao",
            "id_finalidade",
            "finalidade",
            "id_unidade_receptora",
            "unidade_receptora",
            "id_unidade_executora",
            "unidade_executora",
            "id_usuario",
            "id_status_pagamento",
            "status_pagamento",
            "id_beneficiario",
            "beneficiario",
            "id_empenho",
            "empenho",
            "documentos",
            "credito",
            "montante",
            "data_criacao",
        ]

    def validate(self, data):
        finalidade = data.get("finalidade")
        documentos = data.get("documentos", [])
        documentos_id = [doc["tipo_documento"].pk for doc in documentos]
        montante = data.get("montante", None)

        validation_errors = {}
        documentos_validation_errors = []
        montante_validation_errors = []
        empenho_validation_errors = []
        credito_validation_errors = []

        if not montante:
            montante_validation_errors.append("O montante é obrigatório.")

        # docs
        vistos = set()
        for doc in documentos_id:
            if doc not in vistos:
                vistos.add(doc)
            else:
                documentos_validation_errors.append(
                    {
                        "id_tipo_documento": doc,
                        "error": "Não é possível enviar mais de um documento do mesmo tipo.",
                    }
                )

        tipos_documentos_possiveis = (
            finalidade.tipodocumentoparafinalidade_set.select_related(
                "tipo_documento"
            ).all()
        )
        tipos_documentos_possiveis_pk = [
            tipo_doc.tipo_documento.pk for tipo_doc in tipos_documentos_possiveis
        ]

        for tipo_doc in tipos_documentos_possiveis:
            if tipo_doc.obrigatorio and tipo_doc.tipo_documento.pk not in documentos_id:
                documentos_validation_errors.append(
                    {
                        "id_tipo_documento": tipo_doc.tipo_documento.pk,
                        "error": f"O tipo documento '{tipo_doc.tipo_documento.tipo_documento}' é obrigatório para esta finalidade.",
                    }
                )

        for doc in documentos:
            tipo_doc_obj = doc["tipo_documento"]
            if tipo_doc_obj.pk not in tipos_documentos_possiveis_pk:
                documentos_validation_errors.append(
                    {
                        "id_tipo_documento": tipo_doc_obj.pk,
                        "error": f"O tipo de documento '{tipo_doc_obj.tipo_documento}' não é permitido para esta finalidade.",
                    }
                )

        if documentos_validation_errors:
            validation_errors["documentos"] = documentos_validation_errors

        # montante
        id_transacao = data.get("id_transacao")
        unidade_executora = data.get("unidade_executora")
        unidade_receptora = data.get("unidade_receptora")
        empenho = data.get("empenho", None)
        credito = data.get("credito")

        transacao_update = VersaoTransacao.objects.filter(
            transacao_id=id_transacao,
            transacao__versao_transacao=F("id_versao_transacao"),
        ).first()

        montante_unidade = 0.00
        transacao_update_montante = transacao_update.montante if transacao_update else 0

        if finalidade.natureza_finalidade.pk == CUSTEIO:
            montante_unidade = (
                unidade_executora.montante_custeio + transacao_update_montante
            )
        elif finalidade.natureza_finalidade.pk == CAPITAL:
            montante_unidade = (
                unidade_executora.montante_capital + transacao_update_montante
            )

        if not credito and montante_unidade < montante:
            montante_validation_errors.append(
                f"O valor do montante na unidade '{unidade_executora}' é insuficiente. "
                f"Valor do montante de {finalidade.natureza_finalidade} na unidade: {montante_unidade:.2f}."
            )

        if credito and not unidade_executora.pode_empenhar:
            credito_validation_errors.append(
                "Está unidade não tem a permissão para empenhar um valor."
            )

        if not empenho:
            if credito and not unidade_receptora:
                validation_errors["unidade_receptora"] = (
                    "Para realizar uma transferiência de montante é necessário uma unidade receptora."
                )

            if finalidade.id_finalidade not in TRANSFERENCIA_FINALIDADES:
                credito_validation_errors.append(
                    "Esta finalidade não permite tranferência."
                )

            if montante_validation_errors:
                validation_errors["montante"] = montante_validation_errors

            if credito_validation_errors:
                validation_errors["credito"] = credito_validation_errors

            if validation_errors:
                raise serializers.ValidationError(validation_errors)
            return data

        if not empenho.ativo:
            empenho_validation_errors.append(
                "Não é possível criar ou modificar transações de um empenho inativo."
            )

        montante_empenho = empenho.montante

        if transacao_update:  # Somar o valor que tinha sido subtraído.
            montante_empenho += transacao_update.montante

        if not credito and montante > montante_empenho:
            montante_validation_errors.append(
                f"Saldo insuficiente no empenho. O Valor da despesa (R$ {montante:.2f}) "
                f"é maior que o saldo atual (R$ {montante_empenho:.2f})."
            )
        if empenho_validation_errors:
            validation_errors["id_empenho"] = empenho_validation_errors

        if montante_validation_errors:
            validation_errors["montante"] = montante_validation_errors

        if credito_validation_errors:
            validation_errors["credito"] = credito_validation_errors

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        return data

    def create(self, validated_data):
        documentos_data = validated_data.pop("documentos", [])
        user = self.context["request"].user

        versao_transacao = None
        with transaction.atomic():
            versao_transacao = VersaoTransacao.objects.create(
                **validated_data, usuario=user
            )
            docs = [
                ValorDocumento(versao_transacao=versao_transacao, **doc)
                for doc in documentos_data
            ]
            ValorDocumento.objects.bulk_create(docs)

        return versao_transacao


class TransacaoSerializer(serializers.ModelSerializer):
    transacao = VersaoTransacaoSerializer(
        read_only=True, allow_null=False, source="versao_transacao"
    )

    class Meta:
        model = Transacao
        fields = ["id_transacao", "transacao", "data_criacao"]
        read_only_fields = ["id_transacao", "data_criacao"]

    def create(self, validated_data):
        versao_transacao_data = self.initial_data.get("transacao", None)

        with transaction.atomic():
            transacao = Transacao.objects.create(**validated_data)
            if versao_transacao_data is not None:
                versao_transacao_data["id_transacao"] = transacao.pk
                versao_transacao_data["numero_versao"] = 1
                versao_serializer = VersaoTransacaoSerializer(
                    data=versao_transacao_data, context=self.context
                )
                versao_serializer.is_valid(raise_exception=True)
                versao_transacao = versao_serializer.save()
                transacao.versao_transacao = versao_transacao
                transacao.save()

        return transacao

    def update(self, instance, validated_data):

        versao_transacao_data = self.initial_data.get("transacao", None)
        if versao_transacao_data is None:
            raise serializers.ValidationError("Nenhum dado foi atualizado")

        old_docs = [
            {
                "id_tipo_documento": doc.tipo_documento.pk,
                "valor_documento": doc.valor_documento,
            }
            for doc in ValorDocumento.objects.filter(
                versao_transacao=instance.versao_transacao
            )
        ]

        id_finalidade = versao_transacao_data.pop("id_finalidade", None)
        if id_finalidade and instance.versao_transacao.finalidade.pk != id_finalidade:
            tipos_docs = TipoDocumentoParaFinalidade.objects.filter(
                finalidade=id_finalidade
            )
            tipos_docs_id = [doc.tipo_documento.pk for doc in tipos_docs]

            for doc in old_docs.copy():
                if doc["id_tipo_documento"] not in tipos_docs_id:
                    old_docs.remove(doc)

        old_versao_transacao = model_to_dict(
            instance.versao_transacao, exclude=["id_versao_transacao"]
        )
        for field, value in old_versao_transacao.copy().items():
            if field in [
                "transacao",
                "finalidade",
                "unidade_executora",
                "unidade_receptora",
                "usuario",
                "status_pagamento",
                "empenho",
                "beneficiario",
            ]:
                old_versao_transacao.pop(field)
                old_versao_transacao[f"id_{field}"] = value

        new_docs = versao_transacao_data.pop("documentos", [])

        if old_docs or new_docs:
            dados_combinados = {doc["id_tipo_documento"]: doc for doc in old_docs}
            dados_combinados.update({doc["id_tipo_documento"]: doc for doc in new_docs})
            old_versao_transacao["documentos"] = list(dados_combinados.values())

        new_data = {**old_versao_transacao, **versao_transacao_data}
        for field, value in new_data.copy().items():
            if value is None:
                new_data.pop(field)

        with transaction.atomic():
            new_data["numero_versao"] = int(instance.versao_transacao.numero_versao) + 1
            new_data["id_transacao"] = instance.pk
            versao_serializer = VersaoTransacaoSerializer(
                data=new_data, context=self.context
            )
            versao_serializer.is_valid(raise_exception=True)

            versao_transacao = versao_serializer.save()
            instance.versao_transacao = versao_transacao
            instance.save()
        return instance


class EmpenhoSerializer(serializers.ModelSerializer):
    transacoes = serializers.SerializerMethodField()

    class Meta:
        model = Empenho
        fields = [
            "id_empenho",
            "numero_empenho",
            "numero_pen",
            "finalidade",
            "data_criacao",
            "montante",
            "transacoes",
            "ativo",
        ]
        read_only_fields = ["id_empenho", "data_criacao", "montante"]

    def get_transacoes(self, obj):
        queryset = Transacao.objects.filter(versao_transacao__empenho=obj)
        return TransacaoSerializer(queryset, many=True, context=self.context).data
