from despesas.models import ZERO, Lancamento, Natureza, TipoMovimento
from despesas.serializers import UnidadeSaldoSerializer
from django.db.models import Q, Sum
from drf_spectacular.utils import extend_schema
from entidades.models import Centro, Unidade
from rest_framework import serializers, viewsets
from rest_framework.response import Response


class UnidadeSaldoQuerySerializer(serializers.Serializer):
    ano_fiscal = serializers.IntegerField(
        required=False, min_value=1, max_value=32767
    )
    id_unidade_interna = serializers.PrimaryKeyRelatedField(
        queryset=Unidade.objects.all(), required=False
    )
    id_unidades = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Unidade.objects.all()),
        required=False,
        allow_empty=False,
    )
    centro = serializers.PrimaryKeyRelatedField(
        queryset=Centro.objects.all(), required=False
    )

    def validate(self, attrs):
        if not any(
            field in attrs
            for field in (
                "ano_fiscal",
                "id_unidade_interna",
                "id_unidades",
                "centro",
            )
        ):
            raise serializers.ValidationError(
                {
                    "ano_fiscal": (
                        "Informe ano_fiscal, id_unidade_interna, id_unidades ou "
                        "centro para limitar a consulta."
                    )
                }
            )
        return attrs


class UnidadeSaldoViewSet(viewsets.GenericViewSet):
    queryset = Lancamento.objects.none()
    serializer_class = UnidadeSaldoSerializer
    http_method_names = ["get"]

    @extend_schema(
        parameters=[UnidadeSaldoQuerySerializer],
        responses=UnidadeSaldoSerializer(many=True),
    )
    def list(self, request):
        query = UnidadeSaldoQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data

        lancamentos = Lancamento.objects.filter(unidade__isnull=False)
        if "ano_fiscal" in filters:
            lancamentos = lancamentos.filter(ano_fiscal=filters["ano_fiscal"])
        if "id_unidade_interna" in filters:
            lancamentos = lancamentos.filter(
                unidade=filters["id_unidade_interna"]
            )
        if "id_unidades" in filters:
            lancamentos = lancamentos.filter(unidade__in=filters["id_unidades"])
        if "centro" in filters:
            lancamentos = lancamentos.filter(centro=filters["centro"])

        saldos = list(
            lancamentos.values(
                "unidade_id",
                "unidade__nome_unidade",
                "unidade__cod_estruturado",
                "ano_fiscal",
                "natureza_id",
                "natureza__nome",
            )
            .annotate(
                saldo=Sum("montante"),
                gasto_lancamentos=Sum(
                    "montante",
                    filter=Q(tipo_movimento__conta_como_gasto=True),
                ),
                orcamento=Sum(
                    "montante",
                    filter=Q(
                        tipo_movimento__codigo=TipoMovimento.Codigo.DISTRIBUICAO,
                        montante__gt=0,
                    ),
                ),
            )
            .order_by("unidade__cod_estruturado", "ano_fiscal", "natureza_id")
        )

        def amounts(row):
            return {
                **row,
                "saldo": row["saldo"] or ZERO,
                "gasto": -(row["gasto_lancamentos"] or ZERO),
                "orcamento": row["orcamento"] or ZERO,
            }

        saldos = [amounts(row) for row in saldos]

        if (
            "ano_fiscal" in filters
            and "id_unidade_interna" not in filters
            and "id_unidades" not in filters
        ):
            saldos_por_unidade_natureza = {
                (row["unidade_id"], row["natureza_id"]): row
                for row in saldos
            }
            unidades_query = Unidade.objects.order_by("cod_estruturado")
            if "centro" in filters:
                unidades_query = unidades_query.filter(centro=filters["centro"])
            unidades = unidades_query.values(
                "id_unidade_interna", "nome_unidade", "cod_estruturado"
            )
            naturezas = Natureza.objects.order_by("id_natureza").values(
                "id_natureza", "nome"
            )
            saldos = [
                {
                    "unidade_id": unidade["id_unidade_interna"],
                    "unidade__nome_unidade": unidade["nome_unidade"],
                    "unidade__cod_estruturado": unidade["cod_estruturado"],
                    "ano_fiscal": filters["ano_fiscal"],
                    "natureza_id": natureza["id_natureza"],
                    "natureza__nome": natureza["nome"],
                    **{
                        key: saldos_por_unidade_natureza.get(
                            (unidade["id_unidade_interna"], natureza["id_natureza"]),
                            {},
                        ).get(key, ZERO)
                        for key in ("saldo", "gasto", "orcamento")
                    },
                }
                for unidade in unidades
                for natureza in naturezas
            ]

        page = self.paginate_queryset(saldos)
        if page is not None:
            data = self.get_serializer(page, many=True).data
            return self.get_paginated_response(data)
        return Response(self.get_serializer(saldos, many=True).data)
