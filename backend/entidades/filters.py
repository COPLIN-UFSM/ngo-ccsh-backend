from django.db.models import Q
from django_filters import BooleanFilter, CharFilter, FilterSet, NumberFilter

from entidades.models import Servidor, Unidade


class UnidadeFilterSet(FilterSet):
    nome_unidade = CharFilter(field_name="nome_unidade", method="filter_categories")
    cod_estruturado = CharFilter(
        field_name="cod_estruturado", method="filter_categories"
    )
    tipo_unidade = CharFilter(
        field_name="tipo_unidade__tipo_unidade", method="filter_categories"
    )
    centro = CharFilter(field_name="centro__nome_centro", method="filter_categories")

    situacao_unidade = CharFilter(
        field_name="situacao_unidade__situacao_unidade",
        method="filter_categories",
    )

    id_unidade_pai = NumberFilter(field_name="unidade_pai_id")
    id_centro = NumberFilter(field_name="centro_id")
    id_tipo_unidade = NumberFilter(field_name="tipo_unidade_id")
    id_situacao_unidade = NumberFilter(field_name="situacao_unidade_id")

    def filter_categories(self, queryset, name, value):
        categories = [
            category.strip() for category in value.split(",") if category.strip()
        ]
        if not categories:
            return queryset

        condition = Q()
        for category in categories:
            condition |= Q(**{f"{name}__iexact": category})
        return queryset.filter(condition)

    class Meta:
        model = Unidade
        fields = []


class ServidorFilterSet(FilterSet):
    # cpf comes from the related Pessoa model.
    cpf = CharFilter(field_name="pessoa__cpf", lookup_expr="exact")
    ativo = BooleanFilter(field_name="ativo")

    class Meta:
        model = Servidor
        fields = []
