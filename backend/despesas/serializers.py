from rest_framework import serializers

from despesas.models import *


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
        fields = ["id_grupo_finalidade", "grupo_finalidade"]
        read_only_fields = ["id_grupo_finalidade"]


class NaturezaFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturezaFinalidade
        fields = ["id_natureza_finalidade", "natureza_finalidade"]
        read_only_fields = ["id_natureza_finalidade"]


class GrupoFinalidadeField(serializers.RelatedField):

    def to_representation(self, value):
        return GrupoFinalidadeSerializer(value).data

    def to_internal_value(self, data):
        try:
            return GrupoFinalidade.objects.get(pk=data, ativo=True)
        except NaturezaFinalidade.DoesNotExist:
            raise serializers.ValidationError("Não existe nenhum grupo de finalidade com este id.")


class NaturezaFinalidadeField(serializers.RelatedField):

    def to_representation(self, value):
        return NaturezaFinalidadeSerializer(value).data

    def to_internal_value(self, data):
        try:
            return NaturezaFinalidade.objects.get(pk=data, ativo=True)
        except NaturezaFinalidade.DoesNotExist:
            raise serializers.ValidationError("Não existe nenhuma natureza de finalidade com este id.")


class TipoDocumentoParaFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumentoParaFinalidade
        fields = ["pk", "tipo_documento", "obrigatorio"]
        read_only_fields = ['pk']


class FinalidadeSerializer(serializers.ModelSerializer):
    grupo_finalidade = GrupoFinalidadeField(queryset=GrupoFinalidade.objects.all())
    natureza_finalidade = NaturezaFinalidadeField(queryset=NaturezaFinalidade.objects.all())
    tipos_documentos = TipoDocumentoParaFinalidadeSerializer(many=True)

    class Meta:
        model = Finalidade
        fields = [
            "id_finalidade",
            "finalidade",
            "natureza_finalidade",
            "grupo_finalidade",
            "tipos_documentos",
        ]
        read_only_fields = ["id_finalidade"]

    def validate_tipos_documentos(self, value):
        errors_tipos_documentos = []
        for tipo_doc in value:
            try:
                TipoDocumento.objects.get(pk=tipo_doc['tipo_documento'])
            except TipoDocumento.DoesNotExist:
                errors_tipos_documentos.append(
                    f'Não existe nenhum tipo de documento com id {tipo_doc["tipo_documento"]}')
        if len(errors_tipos_documentos) > 0:
            raise serializers.ValidationError(errors_tipos_documentos)

        return value

    def create(self, validated_data):
        tipos_documentos = validated_data.pop("tipos_documentos", [])
        instance = Finalidade.objects.create(**validated_data)
        for tipo_doc in tipos_documentos:
            tipo_documento = TipoDocumento.objects.get(pk=tipo_doc['tipo_documento'])
            TipoDocumentoParaFinalidade.objects.create(tipo_documento=tipo_documento, finalide=instance,
                                                       obrigatorio=tipo_doc['obrigatorio'])
        return instance



class DocumentoNestedSerializer(serializers.ModelSerializer):
    tipo_documento = TipoDocumentoSerializer(read_only=True)
    id_tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all(),
        source="tipo_documento",  # Aponta para o atributo do modelo Django
        write_only=True
    )

    class Meta:
        model = ValorDocumento
        exclude = ["transacao"]


class TransacaoSerializer(serializers.ModelSerializer):
    documentos = DocumentoNestedSerializer(many=True, required=False, allow_empty=True)

    def create(self, validated_data):
        documentos_data = validated_data.pop("documentos", [])
        transacao = Transacao.objects.create(**validated_data)

        for doc_data in documentos_data:
            ValorDocumento.objects.create(transacao=transacao, **doc_data)
        return transacao

    def update(self, instance, validated_data):
        documentos_data = validated_data.pop("documentos", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if documentos_data is not None:
            instance.documentos.all().delete()
            for doc_data in documentos_data:
                ValorDocumento.objects.create(transacao=instance, **doc_data)

        return instance

    class Meta:
        model = Transacao
        fields = [
            "id_transacao",
            "transacao_pai",
            "empenho",
            "finalidade",
            "unidade_credora",
            "unidade_executora",
            "usuario",
            "status",
            "beneficiario_interno",
            "credito",
            "descricao",
            "montante",
            "quantidade",
            "local_trecho",
            "data_criacao",
            "data_modificacao",
            "motivo_modificacao",
            "documentos",
        ]

    def validate(self, data):
        empenho = data.get("empenho")
        montante = data.get("montante")
        id_transacao = data.get("id_transacao")
        eh_credito = data.get("eh_credito")

        if empenho and not empenho.ativo:
            raise serializers.ValidationError(
                {"empenho": "Não é possível criar ou modificar transações de um empenho inativo."}
            )

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
                {
                    "montante": f"Saldo insuficiente. O Valor da despesa (R$ {montante:.2f}) é maior que o saldo atual (R$ {total_despesas:.2f})."}
            )
        return data


class EmpenhoSerializer(serializers.ModelSerializer):
    transacoes = TransacaoSerializer(many=True, read_only=True)
    montante = serializers.SerializerMethodField()

    class Meta:
        model = Empenho
        fields = ["id_empenho", "numero_empenho", "numero_pen", "descricao", "finalidade", "montante", "transacoes"]
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


class StatusTransacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusTransacao
        fields = "__all__"
