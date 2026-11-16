from rest_framework.filters import OrderingFilter


class AliasOrderingFilter(OrderingFilter):
    ordering_aliases = {}

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if ordering is None:
            return None

        aliases = getattr(view, "ordering_aliases", self.ordering_aliases)
        return [
            f"{'-' if field.startswith('-') else ''}"
            f"{aliases.get(field.lstrip('-'), field.lstrip('-'))}"
            for field in ordering
        ]
