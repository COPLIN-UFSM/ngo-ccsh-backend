from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from entidades.models import Centro, Pessoa, Unidade
from rest_framework import serializers

from . import saldos, services
from .models import (
    Empenho,
    Finalidade,
    GrupoFinalidade,
    Lancamento,
    Natureza,
    TipoDocumento,
    TipoDocumentoParaFinalidade,
    TipoMovimento,
    Transacao,
    ValorDocumento,
)


class NaturezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Natureza
        fields = ["id_natureza", "nome", "ativo"]
        read_only_fields = ["id_natureza"]


class GrupoFinalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoFinalidade
        fields = ["id_grupo_finalidade", "nome", "ativo"]
        read_only_fields = ["id_grupo_finalidade"]


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = ["id_tipo_documento", "nome", "tipo_dado", "ativo"]
        read_only_fields = ["id_tipo_documento"]


class TipoDadoDocumentoItemSerializer(serializers.Serializer):
    nome = serializers.CharField()
    codigo = serializers.CharField()


class TipoDadoDocumentoSerializer(serializers.Serializer):
    data = TipoDadoDocumentoItemSerializer(many=True)

    def to_representation(self, instance):
        return {
            "data": [
                {"nome": item[1], "codigo": item[0]}
                for index, item in enumerate(TipoDocumento.TipoDado.choices)
            ]
        }


class TipoMovimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMovimento
        fields = ["id_tipo_movimento", "codigo", "nome"]
        read_only_fields = ["id_tipo_movimento", "codigo", "nome"]


class TipoDocumentoParaFinalidadeSerializer(serializers.ModelSerializer):
    id_tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all(), source="tipo_documento"
    )
    tipo_documento = serializers.CharField(source="tipo_documento.nome", read_only=True)

    ativo = serializers.BooleanField(default=True, required=False)
    obrigatorio = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = TipoDocumentoParaFinalidade
        fields = [
            "id_tipo_documento",
            "tipo_documento",
            "obrigatorio",
            "ativo",
        ]
        read_only_fields = ["id_tipo_documento_para_finalidade"]


class FinalidadeSerializer(serializers.ModelSerializer):
    id_natureza = serializers.PrimaryKeyRelatedField(
        queryset=Natureza.objects.all(), source="natureza"
    )
    natureza = serializers.CharField(source="natureza.nome", read_only=True)
    id_grupo_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=GrupoFinalidade.objects.all(),
        source="grupo",
        required=False,
        allow_null=True,
    )
    grupo = serializers.CharField(source="grupo.nome", read_only=True)
    tipos_documentos = TipoDocumentoParaFinalidadeSerializer(
        source="tipodocumentoparafinalidade_set", many=True, required=False
    )

    class Meta:
        model = Finalidade
        fields = [
            "id_finalidade",
            "nome",
            "id_natureza",
            "natureza",
            "id_grupo_finalidade",
            "grupo",
            "permite_transporte",
            "tipos_documentos",
            "ativo",
        ]
        read_only_fields = ["id_finalidade"]

    @transaction.atomic
    def create(self, validated_data):
        links = validated_data.pop("tipodocumentoparafinalidade_set", [])
        finalidade = Finalidade.objects.create(**validated_data)
        TipoDocumentoParaFinalidade.objects.bulk_create(
            [
                TipoDocumentoParaFinalidade(finalidade=finalidade, **link)
                for link in links
            ]
        )
        return finalidade

    @transaction.atomic
    def update(self, instance, validated_data):
        links = validated_data.pop("tipodocumentoparafinalidade_set", None)
        instance = super().update(instance, validated_data)

        if links is not None:
            fields_errors = []
            all_fields_sum = 0
            for link in links:
                tipo_documento = link.get("tipo_documento", None)
                if not tipo_documento:
                    fields_errors.append(
                        {
                            "id_tipo_documento": "Informe o campo para atualizar ou adicionar."
                        }
                    )
                    all_fields_sum += 1
                else:
                    fields_errors.append({})
                    TipoDocumentoParaFinalidade.objects.update_or_create(
                        finalidade=instance,
                        tipo_documento=link["tipo_documento"],
                        defaults={
                            "obrigatorio": link.get("obrigatorio", True),
                            "ativo": link.get("ativo", True),
                        },
                    )

            if all_fields_sum > 0:
                errors = []
                for i, field_error in enumerate(fields_errors):
                    errors.append({i: field_error})
                raise serializers.ValidationError({"tipos_documentos": errors})
        return instance


class EmpenhoSerializer(serializers.ModelSerializer):
    id_centro = serializers.PrimaryKeyRelatedField(
        queryset=Centro.objects.all(), source="centro"
    )
    id_natureza = serializers.PrimaryKeyRelatedField(
        queryset=Natureza.objects.all(), source="natureza"
    )
    id_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=Finalidade.objects.all(), source="finalidade"
    )
    id_empenho_origem = serializers.PrimaryKeyRelatedField(
        queryset=Empenho.objects.all(),
        source="empenho_origem",
        required=False,
        allow_null=True,
    )
    centro = serializers.StringRelatedField(read_only=True)
    natureza = serializers.StringRelatedField(read_only=True)
    finalidade = serializers.StringRelatedField(read_only=True)

    saldo = serializers.SerializerMethodField()
    gasto = serializers.SerializerMethodField()
    a_complementar = serializers.SerializerMethodField()

    class Meta:
        model = Empenho
        fields = [
            "id_empenho",
            "numero_empenho",
            "numero_pen",
            "id_centro",
            "centro",
            "ano_fiscal",
            "id_natureza",
            "natureza",
            "id_finalidade",
            "finalidade",
            "id_empenho_origem",
            "criado_em",
            "ativo",
            "saldo",
            "gasto",
            "a_complementar",
        ]
        read_only_fields = [
            "id_empenho",
            "criado_em",
            "saldo",
            "gasto",
            "a_complementar",
        ]

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_saldo(self, obj):
        return obj.saldo

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_gasto(self, obj):
        return obj.gasto

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_a_complementar(self, obj):
        return saldos.a_complementar(obj)


class LancamentoSerializer(serializers.ModelSerializer):
    tipo_movimento = serializers.CharField(source="tipo_movimento.nome", read_only=True)
    id_centro = serializers.IntegerField(source="centro_id", read_only=True)
    natureza = serializers.CharField(source="natureza.nome", read_only=True)
    finalidade = serializers.CharField(source="finalidade.nome", read_only=True)

    id_empenho = serializers.IntegerField(source="empenho_id", read_only=True)
    id_unidade = serializers.IntegerField(source="unidade_id", read_only=True)
    id_lancamento_estornado = serializers.IntegerField(
        source="estorna_id", read_only=True
    )

    class Meta:
        model = Lancamento
        fields = [
            "id_lancamento",
            "id_centro",
            "tipo_movimento",
            "ano_fiscal",
            "natureza",
            "id_empenho",
            "id_unidade",
            "finalidade",
            "montante",
            "id_lancamento_estornado",
        ]


class UnidadeSaldoSerializer(serializers.Serializer):
    id_unidade_interna = serializers.IntegerField(source="unidade_id")
    nome_unidade = serializers.CharField(source="unidade__nome_unidade")
    cod_estruturado = serializers.CharField(source="unidade__cod_estruturado")
    ano_fiscal = serializers.IntegerField()
    id_natureza = serializers.IntegerField(source="natureza_id")
    natureza = serializers.CharField(source="natureza__nome")
    saldo = serializers.DecimalField(max_digits=15, decimal_places=2)
    gasto = serializers.DecimalField(max_digits=15, decimal_places=2)
    orcamento = serializers.DecimalField(max_digits=15, decimal_places=2)


class ValorDocumentoSerializer(serializers.ModelSerializer):
    id_tipo_documento = serializers.IntegerField(read_only=True)
    tipo_documento = serializers.CharField(source="tipo_documento.nome", read_only=True)

    class Meta:
        model = ValorDocumento
        fields = [
            "id_valor_documento",
            "id_tipo_documento",
            "tipo_documento",
            "ordem",
            "valor",
        ]


class OperationTransacaoDataItemSerializer(serializers.Serializer):
    nome = serializers.CharField()
    codigo = serializers.CharField()


class OperationTransacaoDataSerializer(serializers.Serializer):
    data = OperationTransacaoDataItemSerializer(
        many=True,
        read_only=True,
        default=[
            {"nome": item[1], "codigo": item[0]}
            for index, item in enumerate(Transacao.Operacao.choices)
        ]
    )


class TransacaoReadSerializer(serializers.ModelSerializer):
    id_usuario = serializers.IntegerField(source="usuario.pk", read_only=True)
    id_beneficiario = serializers.IntegerField(source="beneficiario.pk", read_only=True)
    id_transacao_corrigida = serializers.IntegerField(
        source="corrige_id", read_only=True
    )
    usuario = serializers.StringRelatedField(
        read_only=True, source="usuario.pessoa.nome_pessoa"
    )

    beneficiario = serializers.StringRelatedField(
        read_only=True, source="beneficiario.pessoa.nome_pessoa"
    )

    lancamentos = LancamentoSerializer(many=True, read_only=True)
    documentos = ValorDocumentoSerializer(many=True, read_only=True)

    class Meta:
        model = Transacao
        fields = [
            "id_transacao",
            "operacao",
            "data",
            "criada_em",
            "id_usuario",
            "usuario",
            "justificativa",
            "id_transacao_corrigida",
            "estimada",
            "id_beneficiario",
            "beneficiario",
            "lancamentos",
            "documentos",
        ]


class DocumentoInputSerializer(serializers.Serializer):
    id_tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.filter(ativo=True), source="tipo_documento"
    )
    valor = serializers.CharField(max_length=256, trim_whitespace=True)


class TransacaoOperationSerializer(serializers.Serializer):
    SUPPORTED_OPERATIONS = [
        (Transacao.Operacao.CREDITO, "Crédito"),
        (Transacao.Operacao.REFORCO, "Reforço de empenho"),
        (Transacao.Operacao.DISTRIBUICAO, "Distribuição do centro para unidade"),
        (Transacao.Operacao.TRANSFERENCIA, "Transferência entre unidades"),
        (Transacao.Operacao.DESPESA, "Despesa"),
        (Transacao.Operacao.ANULACAO, "Anulação"),
        (Transacao.Operacao.CONVERSAO, "Conversão de natureza"),
    ]

    operacao = serializers.ChoiceField(choices=SUPPORTED_OPERATIONS)
    data = serializers.DateField(required=False)
    justificativa = serializers.CharField(required=False, allow_blank=True)
    id_centro = serializers.PrimaryKeyRelatedField(
        queryset=Centro.objects.all(), required=False, source="centro"
    )
    ano_fiscal = serializers.IntegerField(required=False, min_value=1)
    id_natureza = serializers.PrimaryKeyRelatedField(
        queryset=Natureza.objects.all(), required=False, source="natureza"
    )
    id_empenho = serializers.PrimaryKeyRelatedField(
        queryset=Empenho.objects.all(), required=False, source="empenho"
    )
    id_empenho_origem = serializers.PrimaryKeyRelatedField(
        queryset=Empenho.objects.all(), required=False, source="empenho_origem"
    )
    id_empenho_destino = serializers.PrimaryKeyRelatedField(
        queryset=Empenho.objects.all(), required=False, source="empenho_destino"
    )
    id_unidade = serializers.PrimaryKeyRelatedField(
        queryset=Unidade.objects.all(),
        required=False,
        allow_null=True,
        source="unidade",
    )
    id_unidade_origem = serializers.PrimaryKeyRelatedField(
        queryset=Unidade.objects.all(), required=False, source="unidade_origem"
    )
    id_unidade_destino = serializers.PrimaryKeyRelatedField(
        queryset=Unidade.objects.all(), required=False, source="unidade_destino"
    )
    id_finalidade = serializers.PrimaryKeyRelatedField(
        queryset=Finalidade.objects.all(), required=False, source="finalidade"
    )
    id_beneficiario = serializers.PrimaryKeyRelatedField(
        queryset=Pessoa.objects.all(),
        required=False,
        allow_null=True,
        source="beneficiario",
    )

    montante = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    extraordinario = serializers.BooleanField(required=False, default=False)
    involuntaria = serializers.BooleanField(required=False, default=False)
    estimada = serializers.BooleanField(required=False, default=False)
    documentos = DocumentoInputSerializer(many=True, required=False)

    def validate(self, attrs):
        operacao = attrs["operacao"]
        required_by_operation = {
            Transacao.Operacao.CREDITO: (
                "centro",
                "ano_fiscal",
                "natureza",
                "montante",
            ),
            Transacao.Operacao.REFORCO: ("empenho", "montante"),
            Transacao.Operacao.DISTRIBUICAO: (
                "centro",
                "ano_fiscal",
                "natureza",
                "unidade",
                "montante",
            ),
            Transacao.Operacao.TRANSFERENCIA: (
                "centro",
                "ano_fiscal",
                "natureza",
                "unidade_origem",
                "unidade_destino",
                "montante",
            ),
            Transacao.Operacao.DESPESA: (
                "empenho",
                "finalidade",
                "montante",
            ),
            Transacao.Operacao.ANULACAO: ("empenho", "montante"),
            Transacao.Operacao.CONVERSAO: (
                "empenho_origem",
                "empenho_destino",
                "montante",
            ),
        }
        missing = [
            field for field in required_by_operation[operacao] if field not in attrs
        ]
        if missing:
            raise serializers.ValidationError(
                {
                    field: "Este campo é obrigatório para esta operação."
                    for field in missing
                }
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        documents = [
            (item["tipo_documento"], item["valor"])
            for item in validated_data.get("documentos", [])
        ]
        operation = validated_data["operacao"]
        kwargs = {
            "usuario": request.user,
            "data": validated_data.get("data"),
            "justificativa": validated_data.get("justificativa", ""),
        }
        try:
            if operation == Transacao.Operacao.CREDITO:
                return services.creditar(
                    validated_data["centro"],
                    validated_data["ano_fiscal"],
                    validated_data["natureza"],
                    validated_data["montante"],
                    extraordinario=validated_data["extraordinario"],
                    **kwargs,
                )
            if operation == Transacao.Operacao.REFORCO:
                return services.reforcar_empenho(
                    validated_data["empenho"], validated_data["montante"], **kwargs
                )
            if operation == Transacao.Operacao.DISTRIBUICAO:
                return services.distribuir(
                    validated_data["centro"],
                    validated_data["ano_fiscal"],
                    validated_data["natureza"],
                    validated_data["unidade"],
                    validated_data["montante"],
                    **kwargs,
                )
            if operation == Transacao.Operacao.TRANSFERENCIA:
                return services.transferir_entre_unidades(
                    validated_data["centro"],
                    validated_data["ano_fiscal"],
                    validated_data["natureza"],
                    validated_data["unidade_origem"],
                    validated_data["unidade_destino"],
                    validated_data["montante"],
                    involuntaria=validated_data["involuntaria"],
                    **kwargs,
                )
            if operation == Transacao.Operacao.ANULACAO:
                return services.anular_empenho(
                    validated_data["empenho"], validated_data["montante"], **kwargs
                )
            if operation == Transacao.Operacao.DESPESA:
                return services.registrar_despesa(
                    validated_data["empenho"],
                    validated_data.get("unidade"),
                    validated_data["finalidade"],
                    validated_data["montante"],
                    beneficiario=validated_data.get("beneficiario"),
                    documentos=documents,
                    estimada=validated_data["estimada"],
                    **kwargs,
                )
            return services.converter_natureza(
                validated_data["empenho_origem"],
                validated_data["empenho_destino"],
                validated_data["montante"],
                unidade=validated_data.get("unidade"),
                **kwargs,
            )
        except (DjangoValidationError, services.RegraDeNegocio) as exc:
            detail = (
                services.detalhe_validacao(exc)
                if isinstance(exc, DjangoValidationError)
                else str(exc)
            )
            raise serializers.ValidationError(detail) from exc


class CorrecaoLinhaSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=TipoMovimento.Codigo.choices)
    centro = serializers.PrimaryKeyRelatedField(queryset=Centro.objects.all())
    ano_fiscal = serializers.IntegerField(min_value=1)
    natureza = serializers.PrimaryKeyRelatedField(queryset=Natureza.objects.all())
    montante = serializers.DecimalField(max_digits=15, decimal_places=2)
    empenho = serializers.PrimaryKeyRelatedField(
        queryset=Empenho.objects.all(), required=False, allow_null=True
    )
    unidade = serializers.PrimaryKeyRelatedField(
        queryset=Unidade.objects.all(), required=False, allow_null=True
    )
    finalidade = serializers.PrimaryKeyRelatedField(
        queryset=Finalidade.objects.all(), required=False, allow_null=True
    )


class TransacaoCorrecaoSerializer(serializers.Serializer):
    justificativa = serializers.CharField(required=False, allow_blank=True)
    data = serializers.DateField(required=False)
    estimada = serializers.BooleanField(required=False)
    beneficiario = serializers.PrimaryKeyRelatedField(
        queryset=Pessoa.objects.all(), required=False, allow_null=True
    )
    linhas = CorrecaoLinhaSerializer(many=True, required=False)
    documentos = DocumentoInputSerializer(many=True, required=False)

    def save(self, *, transacao, usuario):
        data = self.validated_data
        lines = data.get("linhas")
        lines = (
            [services.LinhaSpec(**values) for values in lines]
            if lines is not None
            else None
        )
        documents = data.get("documentos")
        documents = (
            [(item["tipo_documento"], item["valor"]) for item in documents]
            if documents is not None
            else None
        )
        correction_args = {
            "justificativa": data.get("justificativa", ""),
            "data": data.get("data"),
            "estimada": data.get("estimada"),
            "linhas": lines,
            "documentos": documents,
        }
        if "beneficiario" in data:
            correction_args["beneficiario"] = data["beneficiario"]
        try:
            return services.corrigir_transacao(
                transacao,
                usuario,
                **correction_args,
            )
        except (DjangoValidationError, services.RegraDeNegocio) as exc:
            detail = (
                services.detalhe_validacao(exc)
                if isinstance(exc, DjangoValidationError)
                else str(exc)
            )
            raise serializers.ValidationError(detail) from exc
