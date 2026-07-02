from django.db.models import Case, F, Sum, When
from rest_framework import serializers

from despesas.models import *

# TODO here!
# class BeneficiarioSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Beneficiario
#         fields = ["id_beneficiario", "beneficiario_interno", "cpf", "matricula"]
#         read_only_fields = ["id_beneficiario"]


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = ["id_tipo_documento", "tipo_documento"]
        read_only_fields = ["id_tipo_documento"]


class DocumentoSerializer(serializers.ModelSerializer):

    tipo_documento  = TipoDocumentoSerializer(read_only=True)

    id_tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all(),
        source="tipo_documento",  # Aponta para o atributo do modelo Django
        write_only=True
    )
    class Meta:
        model = Documento
        fields = ["id_documento", "id_tipo_documento", "tipo_documento", "documento", "transacao", "descricao"]
        read_only_fields = ["id_documento"]


class TipoFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoFinalidade
        fields = ["id_grupo_finalidade", "grupo_finalidade"]
        read_only_fields = ["id_grupo_finalidade"]


class NaturezaFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturezaFinalidade
        fields = ["id_natureza_finalidade", "natureza_finalidade"]
        read_only_fields = ["id_natureza_finalidade"]


class FinalidadeSerializer(serializers.ModelSerializer):
    natureza_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=NaturezaFinalidade.objects.all(),
        write_only=True,
        error_messages={
            "does_not_exist": "Código de despesa inexistente.",
            "incorrect_type": "Formato de dado inválido para o tipo de despesa.",
        },
    )

    tipo_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=GrupoFinalidade.objects.all(),
        write_only=True,
        error_messages={
            "does_not_exist": "Código da categoria da finalidade inexistente.",
            "incorrect_type": "Formato de dado inválido para a categoria da finalidade.",
        },
    )

    natureza_finalidade_detail = NaturezaFinalidadeSerializer(source="natureza_finalidade", read_only=True)
    tipo_finalidade_detail = TipoFinalidadeSerializer(source="grupo_finalidade", read_only=True)

    class Meta:
        model = Finalidade
        fields = [
            "id_finalidade",
            "finalidade",
            "natureza_finalidade",
            "natureza_finalidade_detail",
            "tipo_finalidade",
            "tipo_finalidade_detail",
            "modalidade",
        ]
        read_only_fields = ["id_finalidade"]


class SubunidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = ["id_unidade", "nome_unidade", "grupo"]
        read_only_fields = ["id_unidade"]


class DocumentoNestedSerializer(serializers.ModelSerializer):
    tipo_documento  = TipoDocumentoSerializer(read_only=True)
    id_tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all(),
        source="tipo_documento",  # Aponta para o atributo do modelo Django
        write_only=True
    )
    
    class Meta:
        model = Documento
        exclude = ["transacao"]


class TransacaoSerializer(serializers.ModelSerializer):
    documentos = DocumentoNestedSerializer(many=True, required=False, allow_empty=True)

    def create(self, validated_data):
        documentos_data = validated_data.pop("documentos", [])
        transacao = Transacao.objects.create(**validated_data)

        for doc_data in documentos_data:
            Documento.objects.create(transacao=transacao, **doc_data)
        return transacao

    def update(self, instance, validated_data):
        documentos_data = validated_data.pop("documentos", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if documentos_data is not None:
            instance.documentos.all().delete()
            for doc_data in documentos_data:
                Documento.objects.create(transacao=instance, **doc_data)

        return instance

    class Meta:
        model = Transacao
        fields = [
            "id_transacao",
            "transacao_pai",
            "empenho",
            "finalidade",
            "subunidade_credora",
            "subunidade_executora",
            "usuario",
            "status",
            "beneficiario_interno",
            "credito",
            "descricao",
            "montante",
            "quantidade",
            "local_trecho",
            "data_lancamento",
            "data_modificacao",
            "motivo_modificacao",
            "documentos",
        ]

    def validate(self, data):
        empenho = data.get("empenho")
        montante = data.get("montante")
        id_transacao = data.get("id_transacao")
        eh_credito = data.get("eh_credito")

        queryset = Transacao.objects.filter(empenho=empenho)
        if self.instance:
            queryset = queryset.exclude(id_transacao=id_transacao)

        total_despesas = (
            queryset.aggregate(
                total=Sum(
                    Case(
                        When(eh_credito=True, then=F("montante")),
                        When(eh_credito=False, then=-F("montante")),
                    )
                )
            )["total"]
            or 0.00
        )

        if not eh_credito and montante > total_despesas:
            raise serializers.ValidationError(
                {"montante": f"Saldo insuficiente. O Valor da despesa (R$ {montante:.2f}) é maior que o saldo atual (R$ {total_despesas:.2f})."}
            )
        return data


class EmpenhoSerializer(serializers.ModelSerializer):
    transacoes = TransacaoSerializer(many=True, read_only=True)
    montante = serializers.SerializerMethodField()

    class Meta:
        model = Empenho
        fields = ["id_empenho", "empenho", "pen", "descricao", "finalidade", "montante", "transacoes"]
        read_only_fields = ["id_empenho"]

    def get_montante(self, obj):

        valor_somado = (
            Transacao.objects.filter(empenho=obj).aggregate(
                total=Sum(
                    Case(
                        When(eh_credito=True, then=F("montante")),
                        When(eh_credito=False, then=-F("montante")),
                    )
                )
            )["total"]
            or 0.00
        )

        return valor_somado


# Finalidade em empenho? Finalidade em Transação.
