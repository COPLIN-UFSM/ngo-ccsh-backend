from django_filters import CharFilter, FilterSet, NumberFilter

from .models import Empenho, Finalidade, GrupoFinalidade, Natureza, TipoDocumento


class ActiveFilterSet(FilterSet):
    ativo = CharFilter(method="filter_active")

    def filter_active(self, queryset, name, value):
        if value == "all":
            return queryset
        if value == "false":
            return queryset.filter(ativo=False)
        if value == "true":
            return queryset.filter(ativo=True)
        return queryset.none()


class NaturezaFilterSet(ActiveFilterSet):
    nome = CharFilter(field_name="nome", lookup_expr="icontains")

    class Meta:
        model = Natureza
        fields = []


class GrupoFinalidadeFilterSet(ActiveFilterSet):
    nome = CharFilter(field_name="nome", lookup_expr="icontains")

    class Meta:
        model = GrupoFinalidade
        fields = []


class FinalidadeFilterSet(ActiveFilterSet):
    nome = CharFilter(field_name="nome", lookup_expr="icontains")
    natureza = NumberFilter(field_name="natureza_id")
    grupo = NumberFilter(field_name="grupo_id")

    class Meta:
        model = Finalidade
        fields = []


class TipoDocumentoFilterSet(ActiveFilterSet):
    nome = CharFilter(field_name="nome", lookup_expr="icontains")

    class Meta:
        model = TipoDocumento
        fields = []


class EmpenhoFilterSet(ActiveFilterSet):
    numero_empenho = CharFilter(field_name="numero_empenho", lookup_expr="icontains")
    centro = NumberFilter(field_name="centro_id")
    ano_fiscal = NumberFilter(field_name="ano_fiscal")
    natureza = NumberFilter(field_name="natureza_id")
    finalidade = NumberFilter(field_name="finalidade_id")

    class Meta:
        model = Empenho
        fields = []
