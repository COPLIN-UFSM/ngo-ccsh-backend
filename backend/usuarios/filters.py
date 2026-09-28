from django_filters import CharFilter

from usuarios.models import Usuario
from django_filters import FilterSet

class BaseFilterSet(FilterSet):
    def filter_ativo(self, queryset, name, value, **kwargs):
        if value == 'all':
            return queryset
        elif value == 'false':
            return queryset.filter(ativo=False)
        return queryset.filter(ativo=True)

class UserFilterSet(BaseFilterSet):
    ativo = CharFilter(method='filter_ativo')
    cpf = CharFilter(field_name='cpf', lookup_expr='icontains')
    email = CharFilter(field_name='email', lookup_expr='icontains')
    nome_pessoa = CharFilter(field_name='pessoa__nome_pessoa', lookup_expr='icontains')

    class Meta:
        model = Usuario
        fields = []