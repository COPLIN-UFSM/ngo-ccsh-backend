from django.apps import apps
from django.db import IntegrityError, models, transaction


class ResolveFromSIEQuerySet(models.QuerySet):
    """
    Antes de filtrar, importa do SIE os registros que casam com o filtro e ainda não
    possuem cópia interna. ``get``, ``get_or_create``, ``first``, ``exists`` etc.
    passam por ``filter``, então são cobertos. ``exclude``, ``all`` e filtros com
    ``Q`` ou por campos que só existem no modelo interno (ex.: ``pk``) não importam.

    O pk (interno) nunca é interpretado como pk do SIE; o id do SIE só é usado via
    o campo de vínculo (ex.: ``pessoa_sie=...``).
    """

    def filter(self, *args, **kwargs):
        if kwargs:
            self.model.objects.import_matching_from_sie(**kwargs)
        return super().filter(*args, **kwargs)


class ResolveFromSIEManager(models.Manager.from_queryset(ResolveFromSIEQuerySet)):
    sie_model_name = None
    # Nome do campo (OneToOne) que aponta para o registro do SIE
    sie_link_field = None
    # Campos com o mesmo nome e significado no modelo interno e no SIE
    sie_shared_fields = ()

    @property
    def sie_model(self):
        return apps.get_model("entidades", self.sie_model_name)

    def import_from_sie(self, sie_obj):
        raise NotImplementedError

    def _translate_lookups(self, lookups):
        """Converte lookups do modelo interno para o SIE; None se não for possível."""
        translated = {}
        for key, value in lookups.items():
            base, sep, rest = key.partition("__")
            if base in (self.sie_link_field, f"{self.sie_link_field}_id"):
                if isinstance(value, models.Model):
                    value = value.pk
                translated["pk" + sep + rest] = value
            elif base in self.sie_shared_fields:
                translated[key] = value
            else:
                return None
        return translated

    def import_matching_from_sie(self, **lookups):
        sie_lookups = self._translate_lookups(lookups)
        if not sie_lookups:
            return

        sie_objs = list(self.sie_model.objects.filter(**sie_lookups))
        if not sie_objs:
            return

        # _base_manager evita recursão por este manager
        existentes = set(
            self.model._base_manager.filter(
                **{f"{self.sie_link_field}__in": [s.pk for s in sie_objs]}
            ).values_list(f"{self.sie_link_field}_id", flat=True)
        )
        for sie in sie_objs:
            if sie.pk in existentes:
                continue
            try:
                with transaction.atomic():
                    self.import_from_sie(sie)
            except IntegrityError:
                # Cópia criada concorrentemente ou conflito de chave única
                pass


class PessoaManager(ResolveFromSIEManager):
    sie_model_name = "PessoaSIE"
    sie_link_field = "pessoa_sie"
    sie_shared_fields = ("nome_pessoa", "cpf", "rg")

    def import_from_sie(self, pessoa):
        return self.create(
            pessoa_sie=pessoa,
            nome_pessoa=pessoa.nome_pessoa,
            cpf=pessoa.cpf,
            rg=pessoa.rg,
        )


class CentroManager(ResolveFromSIEManager):
    sie_model_name = "CentroSIE"
    sie_link_field = "centro_sie"
    sie_shared_fields = ("nome_centro", "sigla_centro", "cod_estruturado")

    def import_from_sie(self, centro):
        return self.create(
            centro_sie=centro,
            nome_centro=centro.nome_centro,
            sigla_centro=centro.sigla_centro,
            cod_estruturado=centro.cod_estruturado,
        )


class UnidadeManager(ResolveFromSIEManager):
    sie_model_name = "UnidadeSIE"
    sie_link_field = "unidade_sie"
    sie_shared_fields = ("nome_unidade", "cod_estruturado")

    def import_from_sie(self, unidade):
        return self.create(
            unidade_sie=unidade,
            nome_unidade=unidade.nome_unidade,
            cod_estruturado=unidade.cod_estruturado,
            centro=unidade.centro,
            tipo_unidade=unidade.tipo_unidade,
            situacao_unidade=unidade.situacao_unidade,
        )
