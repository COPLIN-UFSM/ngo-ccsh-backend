from django_filters import BooleanFilter, CharFilter, FilterSet

from entidades.models import Servidor, Unidade


class UnidadeFilterSet(FilterSet):
    nome_unidade = CharFilter(field_name="nome_unidade", lookup_expr="icontains")
    cod_estruturado = CharFilter(field_name="cod_estruturado", lookup_expr="icontains")
    tipo_unidade = CharFilter(field_name="tipo_unidade", lookup_expr="icontains")
    centro = CharFilter(field_name="centro", lookup_expr="icontains")

    situacao_unidade = CharFilter(
        field_name="situacao_unidade", lookup_expr="icontains"
    )

    pode_empenhar = BooleanFilter(field_name="pode_empenhar")

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
