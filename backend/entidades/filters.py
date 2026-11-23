from django_filters import BooleanFilter, CharFilter, FilterSet, NumberFilter

from entidades.models import Servidor, Unidade


class UnidadeFilterSet(FilterSet):
    nome_unidade = CharFilter(field_name="nome_unidade", lookup_expr="icontains")
    cod_estruturado = CharFilter(field_name="cod_estruturado", lookup_expr="icontains")
    tipo_unidade = CharFilter(field_name="tipo_unidade__tipo_unidade", lookup_expr="icontains")
    centro = CharFilter(field_name="centro__nome_centro", lookup_expr="icontains")

    situacao_unidade = CharFilter(
        field_name="situacao_unidade__situacao_unidade", lookup_expr="icontains"
    )

    id_unidade_pai = NumberFilter(field_name="id_unidade_pai")
    id_centro = NumberFilter(field_name="centro_id")
    id_tipo_unidade = NumberFilter(field_name="tipo_unidade_id")
    id_situacao_unidade = NumberFilter(field_name="situacao_unidade_id")

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
