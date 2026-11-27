import logging

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction

logger = logging.getLogger(__name__)


def import_sie_contacts(pessoa, pessoa_sie, emails=None, telefones=None):
    """Add missing SIE contacts without overwriting existing contacts."""
    email_model = apps.get_model("entidades", "Email")
    telefone_model = apps.get_model("entidades", "Telefone")
    email_sie_model = apps.get_model("entidades", "EmailSIE")
    telefone_sie_model = apps.get_model("entidades", "TelefoneSIE")

    if emails is None:
        emails = email_sie_model.objects.filter(
            pessoa_sie_id=pessoa_sie.pk
        ).values_list("email", flat=True)
    if telefones is None:
        telefones = telefone_sie_model.objects.filter(
            pessoa_sie_id=pessoa_sie.pk
        ).values_list("telefone", flat=True)

    result = {
        "emails_created": 0,
        "email_conflicts": 0,
        "invalid_emails": 0,
        "telefones_created": 0,
        "invalid_telefones": 0,
    }

    email_field = email_model._meta.get_field("email")
    for raw_email in emails:
        try:
            email = email_field.clean(str(raw_email).strip(), None)
        except ValidationError:
            result["invalid_emails"] += 1
            continue

        existing = email_model._base_manager.filter(email=email).first()
        if existing is not None:
            if existing.pessoa_id != pessoa.pk:
                result["email_conflicts"] += 1
            continue

        try:
            with transaction.atomic():
                email_model._base_manager.create(pessoa=pessoa, email=email)
            result["emails_created"] += 1
        except IntegrityError:
            existing = email_model._base_manager.filter(email=email).first()
            if existing is None:
                raise
            if existing.pessoa_id != pessoa.pk:
                result["email_conflicts"] += 1

    telefone_field = telefone_model._meta.get_field("telefone")
    for raw_telefone in telefones:
        try:
            telefone = telefone_field.clean(str(raw_telefone).strip(), None)
        except ValidationError:
            result["invalid_telefones"] += 1
            continue

        if telefone_model._base_manager.filter(
            pessoa_id=pessoa.pk, telefone=telefone
        ).exists():
            continue
        telefone_model._base_manager.create(pessoa=pessoa, telefone=telefone)
        result["telefones_created"] += 1

    if result["email_conflicts"]:
        logger.warning(
            "Skipped %s SIE email contact(s) already assigned to another person "
            "for SIE person id %s.",
            result["email_conflicts"],
            pessoa_sie.pk,
        )
    if result["invalid_emails"]:
        logger.warning(
            "Skipped %s invalid SIE email contact(s) for SIE person id %s.",
            result["invalid_emails"],
            pessoa_sie.pk,
        )
    if result["invalid_telefones"]:
        logger.warning(
            "Skipped %s invalid SIE phone contact(s) for SIE person id %s.",
            result["invalid_telefones"],
            pessoa_sie.pk,
        )

    return result


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
        internal_person = self.create(
            pessoa_sie=pessoa,
            nome_pessoa=pessoa.nome_pessoa,
            cpf=pessoa.cpf,
            rg=pessoa.rg,
        )
        import_sie_contacts(internal_person, pessoa)
        return internal_person


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
