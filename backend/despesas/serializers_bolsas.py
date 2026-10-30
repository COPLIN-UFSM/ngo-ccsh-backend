from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from despesas import services
from despesas.models import (
    Empenho,
    Finalidade,
    ItemListaSIAFI,
    ListaSIAFI,
    Natureza,
    ParcelaBolsa,
    VinculoBolsa,
)
from entidades.models import Centro, Pessoa, Unidade


class VinculoBolsaSerializer(serializers.ModelSerializer):
    bolsista = serializers.PrimaryKeyRelatedField(queryset=Pessoa.objects.all())
    unidade = serializers.PrimaryKeyRelatedField(queryset=Unidade.objects.all())
    finalidade = serializers.PrimaryKeyRelatedField(queryset=Finalidade.objects.all())

    class Meta:
        model = VinculoBolsa
        fields = [
            "id_vinculo_bolsa",
            "bolsista",
            "unidade",
            "finalidade",
            "valor_mensal",
            "inicio",
            "fim",
        ]
        read_only_fields = ["id_vinculo_bolsa"]

    def validate(self, attrs):
        valor = attrs.get("valor_mensal")
        inicio = attrs.get("inicio")
        fim = attrs.get("fim")
        if valor is not None and valor <= 0:
            raise serializers.ValidationError(
                {"valor_mensal": "O valor mensal precisa ser maior que zero."}
            )
        if inicio is not None and fim is not None and fim < inicio:
            raise serializers.ValidationError(
                {"fim": "A data final precisa ser igual ou posterior à inicial."}
            )
        return attrs

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc


class ParcelaBolsaSerializer(serializers.ModelSerializer):
    id_vinculo_bolsa = serializers.IntegerField(source="vinculo_id", read_only=True)
    empenho_previsto = serializers.IntegerField(
        source="empenho_previsto_id", read_only=True
    )

    class Meta:
        model = ParcelaBolsa
        fields = [
            "id_parcela_bolsa",
            "id_vinculo_bolsa",
            "competencia",
            "ano_fiscal",
            "valor",
            "status",
            "empenho_previsto",
        ]
        read_only_fields = fields


class ParcelaAlocacaoSerializer(serializers.Serializer):
    empenho_previsto = serializers.PrimaryKeyRelatedField(
        queryset=Empenho.objects.all(), required=False, allow_null=True
    )

    def save(self, *, parcela):
        try:
            return services.alocar_parcela(
                parcela, self.validated_data.get("empenho_previsto")
            )
        except (DjangoValidationError, services.RegraDeNegocio) as exc:
            detail = exc.messages if isinstance(exc, DjangoValidationError) else str(exc)
            raise serializers.ValidationError(detail) from exc


class ItemListaSIAFISerializer(serializers.ModelSerializer):
    parcela = serializers.IntegerField(source="parcela_id", read_only=True)
    bolsista = serializers.CharField(
        source="parcela.vinculo.bolsista.nome_pessoa", read_only=True
    )
    competencia = serializers.DateField(source="parcela.competencia", read_only=True)

    class Meta:
        model = ItemListaSIAFI
        fields = ["id_item_lista_siafi", "parcela", "bolsista", "competencia", "valor"]
        read_only_fields = fields


class ListaSIAFIReadSerializer(serializers.ModelSerializer):
    centro = serializers.IntegerField(source="centro_id", read_only=True)
    transacao = serializers.IntegerField(source="transacao_id", read_only=True)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    itens = ItemListaSIAFISerializer(many=True, read_only=True)

    class Meta:
        model = ListaSIAFI
        fields = [
            "id_lista_siafi",
            "centro",
            "competencia",
            "ano_fiscal",
            "numero_siafi",
            "status",
            "transacao",
            "criada_em",
            "total",
            "itens",
        ]
        read_only_fields = fields


class ListaSIAFICreateSerializer(serializers.Serializer):
    centro = serializers.PrimaryKeyRelatedField(queryset=Centro.objects.all())
    competencia = serializers.DateField()

    def create(self, validated_data):
        return services.criar_lista(**validated_data)


class ListaSIAFIIncluirParcelasSerializer(serializers.Serializer):
    parcelas = serializers.PrimaryKeyRelatedField(
        queryset=ParcelaBolsa.objects.all(), many=True, allow_empty=False
    )

    def save(self, *, lista):
        try:
            return services.incluir_parcelas(lista, self.validated_data["parcelas"])
        except (DjangoValidationError, services.RegraDeNegocio) as exc:
            detail = exc.messages if isinstance(exc, DjangoValidationError) else str(exc)
            raise serializers.ValidationError(detail) from exc


class DivisaoEmpenhoSerializer(serializers.Serializer):
    empenho = serializers.PrimaryKeyRelatedField(queryset=Empenho.objects.all())
    valor = serializers.DecimalField(max_digits=15, decimal_places=2)


class DivisaoParcelaSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ItemListaSIAFI.objects.all())
    partes = DivisaoEmpenhoSerializer(many=True, allow_empty=False)


class ListaSIAFIPagamentoSerializer(serializers.Serializer):
    numero_siafi = serializers.CharField(max_length=64, trim_whitespace=True)
    divisoes = DivisaoParcelaSerializer(many=True, required=False)

    def save(self, *, lista, usuario):
        divisoes = {}
        for entry in self.validated_data.get("divisoes", []):
            item = entry["item"]
            if item.lista_id != lista.pk:
                raise serializers.ValidationError(
                    {"divisoes": f"O item {item.pk} não pertence a esta lista."}
                )
            if item.pk in divisoes:
                raise serializers.ValidationError(
                    {"divisoes": f"O item {item.pk} foi informado mais de uma vez."}
                )
            divisoes[item.pk] = [
                (parte["empenho"], parte["valor"]) for parte in entry["partes"]
            ]
        try:
            return services.pagar_lista(
                lista,
                usuario,
                self.validated_data["numero_siafi"],
                divisoes=divisoes,
            )
        except (DjangoValidationError, services.RegraDeNegocio) as exc:
            detail = exc.messages if isinstance(exc, DjangoValidationError) else str(exc)
            raise serializers.ValidationError(detail) from exc


class DestinoSaldoSerializer(serializers.Serializer):
    acao = serializers.ChoiceField(choices=[services.TRANSPORTAR, services.DEVOLVER])
    montante = serializers.DecimalField(max_digits=15, decimal_places=2)
    empenho = serializers.PrimaryKeyRelatedField(
        queryset=Empenho.objects.all(), required=False, allow_null=True
    )
    unidade = serializers.PrimaryKeyRelatedField(
        queryset=Unidade.objects.all(), required=False, allow_null=True
    )
    novo_empenho = serializers.PrimaryKeyRelatedField(
        queryset=Empenho.objects.all(), required=False, allow_null=True
    )
    natureza = serializers.PrimaryKeyRelatedField(
        queryset=Natureza.objects.all(), required=False, allow_null=True
    )


class FecharExercicioSerializer(serializers.Serializer):
    centro = serializers.PrimaryKeyRelatedField(queryset=Centro.objects.all())
    ano_fiscal = serializers.IntegerField(min_value=1, max_value=32767)
    destinos = DestinoSaldoSerializer(many=True, allow_empty=True)


class ReabrirExercicioSerializer(serializers.Serializer):
    centro = serializers.PrimaryKeyRelatedField(queryset=Centro.objects.all())
    ano_fiscal = serializers.IntegerField(min_value=1, max_value=32767)
    justificativa = serializers.CharField(allow_blank=False, trim_whitespace=True)
