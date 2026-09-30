
class AtivoListDefaultMixin:
    """
    Mixin para gerenciar entidades que usam controle de 'ativo'.
    - Filtra por ativo=True na listagem por padrão.
    - Transforma a deleção física em deleção lógica (Soft Delete).
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list' and 'ativo' not in self.request.query_params:
            return queryset.filter(ativo=True)
        return queryset

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save()