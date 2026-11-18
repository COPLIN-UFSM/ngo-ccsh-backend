from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from django_filters import (
    CharFilter,
    DateTimeFilter,
    FilterSet,
    NumberFilter,
)

from .models import (
    Empenho,
    Finalidade,
    GrupoFinalidade,
    Lancamento,
    Natureza,
    ParcelaBolsa,
    TipoDocumento,
    Transacao,
    VinculoBolsa,
)


def _selected_values(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def _filter_text_choices(queryset, field_name, value, *, contains=False):
    condition = Q()
    for selected in _selected_values(value):
        lookup = "icontains" if contains else "iexact"
        condition |= Q(**{f"{field_name}__{lookup}": selected})
    return queryset.filter(condition).distinct() if condition else queryset


def _filter_related_choices(
    queryset, relation_field, relation_id_field, value, *, allow_null=False
):
    condition = Q()
    for selected in _selected_values(value):
        if allow_null and selected.casefold() in {"null", "none"}:
            condition |= Q(**{f"{relation_field}__isnull": True})
        elif selected.isdecimal():
            condition |= Q(**{relation_id_field: int(selected)})
        else:
            condition |= Q(**{f"{relation_field}__nome__iexact": selected})
    return queryset.filter(condition).distinct() if condition else queryset


class DateRangeValueFilter(DateTimeFilter):
    def filter(self, queryset, value):
        if value is None:
            return queryset

        date_value = (
            timezone.localtime(value).date()
            if timezone.is_aware(value)
            else value.date()
        )
        lookup = f"{self.field_name}__{self.lookup_expr}"
        queryset = queryset.filter(**{lookup: date_value})
        return queryset.distinct() if self.distinct else queryset


def _filter_nullable_ids(queryset, field_name, value):
    ids = []
    include_null = False
    for selected in _selected_values(value):
        if selected.casefold() in {"null", "none"}:
            include_null = True
            continue
        try:
            ids.append(int(selected))
        except ValueError as exc:
            raise ValidationError(f"Valor inválido para {field_name}: {selected}") from exc

    condition = Q()
    if ids:
        condition |= Q(**{f"{field_name}_id__in": ids})
    if include_null:
        condition |= Q(**{f"{field_name}__isnull": True})
    return queryset.filter(condition) if condition else queryset


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
    nome = CharFilter(method="filter_nome")

    def filter_nome(self, queryset, name, value):
        return _filter_text_choices(queryset, name, value, contains=True)

    class Meta:
        model = Natureza
        fields = []


class GrupoFinalidadeFilterSet(ActiveFilterSet):
    nome = CharFilter(method="filter_nome")

    def filter_nome(self, queryset, name, value):
        return _filter_text_choices(queryset, name, value, contains=True)

    class Meta:
        model = GrupoFinalidade
        fields = []


class FinalidadeFilterSet(ActiveFilterSet):
    nome = CharFilter(method="filter_nome")
    natureza = CharFilter(method="filter_natureza")
    grupo = CharFilter(method="filter_grupo")

    def filter_nome(self, queryset, name, value):
        return _filter_text_choices(queryset, name, value, contains=True)

    def filter_natureza(self, queryset, name, value):
        return _filter_related_choices(
            queryset, "natureza", "natureza_id", value
        )

    def filter_grupo(self, queryset, name, value):
        return _filter_related_choices(
            queryset, "grupo", "grupo_id", value, allow_null=True
        )

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


class TransacaoFilterSet(FilterSet):
    id_transacao = NumberFilter(field_name="id_transacao")
    id_transacao_min = NumberFilter(field_name="id_transacao", lookup_expr="gte")
    id_transacao_max = NumberFilter(field_name="id_transacao", lookup_expr="lte")
    operacao = CharFilter(method="filter_operacao")
    data_after = DateRangeValueFilter(field_name="data", lookup_expr="gte")
    data_before = DateRangeValueFilter(field_name="data", lookup_expr="lte")
    criada_em_after = DateRangeValueFilter(
        field_name="criada_em__date", lookup_expr="gte"
    )
    criada_em_before = DateRangeValueFilter(
        field_name="criada_em__date", lookup_expr="lte"
    )
    montante_min = NumberFilter(field_name="montante", lookup_expr="gte")
    montante_max = NumberFilter(field_name="montante", lookup_expr="lte")
    usuario = NumberFilter(field_name="usuario_id")
    beneficiario = NumberFilter(field_name="beneficiario_id")
    centro = NumberFilter(method="filter_centro")
    ano_fiscal = NumberFilter(method="filter_ano_fiscal")

    def filter_operacao(self, queryset, name, value):
        return _filter_text_choices(queryset, name, value)

    def filter_centro(self, queryset, name, value):
        linhas_do_centro = Lancamento.objects.filter(
            transacao_id=OuterRef("pk"), centro_id=value
        )
        return queryset.filter(Exists(linhas_do_centro))

    def filter_ano_fiscal(self, queryset, name, value):
        linhas_do_ano = Lancamento.objects.filter(
            transacao_id=OuterRef("pk"), ano_fiscal=value
        )
        return queryset.filter(Exists(linhas_do_ano))

    class Meta:
        model = Transacao
        fields = []


class VinculoBolsaFilterSet(FilterSet):
    bolsista = NumberFilter(field_name="bolsista_id")
    unidade = NumberFilter(field_name="unidade_id")
    finalidade = NumberFilter(field_name="finalidade_id")
    centro = NumberFilter(field_name="unidade__centro_id")
    ano_fiscal = NumberFilter(method="filter_ano_fiscal")

    def filter_ano_fiscal(self, queryset, name, value):
        return queryset.filter(
            inicio__year__lte=value,
            fim__year__gte=value,
        )

    class Meta:
        model = VinculoBolsa
        fields = []


class ParcelaBolsaFilterSet(FilterSet):
    vinculo = NumberFilter(field_name="vinculo_id")
    ano_fiscal = NumberFilter(field_name="ano_fiscal")
    status = CharFilter(field_name="status")
    competencia = CharFilter(field_name="competencia")
    lista = NumberFilter(field_name="lista_id")
    centro = NumberFilter(field_name="vinculo__unidade__centro_id")

    class Meta:
        model = ParcelaBolsa
        fields = []


class LancamentoFilterSet(FilterSet):
    id_lancamento_min = NumberFilter(field_name="id_lancamento", lookup_expr="gte")
    id_lancamento_max = NumberFilter(field_name="id_lancamento", lookup_expr="lte")
    id_empenho_min = NumberFilter(field_name="empenho_id", lookup_expr="gte")
    id_empenho_max = NumberFilter(field_name="empenho_id", lookup_expr="lte")
    id_unidade = CharFilter(method="filter_id_unidade")
    centro = NumberFilter(field_name="centro_id")
    ano_fiscal_min = NumberFilter(field_name="ano_fiscal", lookup_expr="gte")
    ano_fiscal_max = NumberFilter(field_name="ano_fiscal", lookup_expr="lte")
    natureza = CharFilter(method="filter_natureza")
    tipo_movimento = CharFilter(method="filter_tipo_movimento")
    finalidade = CharFilter(method="filter_finalidade")
    id_lancamento_estornado_min = NumberFilter(
        field_name="estorna_id", lookup_expr="gte"
    )
    id_lancamento_estornado_max = NumberFilter(
        field_name="estorna_id", lookup_expr="lte"
    )
    montante_min = NumberFilter(field_name="montante", lookup_expr="gte")
    montante_max = NumberFilter(field_name="montante", lookup_expr="lte")

    def filter_id_unidade(self, queryset, name, value):
        return _filter_nullable_ids(queryset, "unidade", value)

    def filter_natureza(self, queryset, name, value):
        return _filter_text_choices(queryset, "natureza__nome", value)

    def filter_tipo_movimento(self, queryset, name, value):
        return _filter_text_choices(queryset, "tipo_movimento__nome", value)

    def filter_finalidade(self, queryset, name, value):
        return _filter_related_choices(
            queryset, "finalidade", "finalidade_id", value, allow_null=True
        )

    class Meta:
        model = Lancamento
        fields = []
