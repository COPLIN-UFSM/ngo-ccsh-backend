from django.db import models
from django.apps import apps
from django.db import IntegrityError, transaction


class ResolveFromSIEQuerySet(models.QuerySet):
    def get(self, *args, **kwargs):
        try:
            return super().get(*args, **kwargs)
        except self.model.DoesNotExist:
            pass

        if args:
            raise NotImplementedError("Ainda não há suporte para argumentos.")

        self.model.objects._import_if_needed(**kwargs)
        return super().get(*args, **kwargs)


class ResolveFromSIEManager(models.Manager.from_queryset(ResolveFromSIEQuerySet)):
    sie_model_name = None

    @property
    def sie_model(self):
        return apps.get_model("entidades", self.sie_model_name)

    def import_from_sie(self, sie_obj):
        raise NotImplementedError

    def _import_if_needed(self, **kwargs):
        try:
            sie = self.sie_model.objects.get(**kwargs)
        except self.sie_model.DoesNotExist:
            raise self.model.DoesNotExist

        try:
            with transaction.atomic():
                self.import_from_sie(sie)
        except IntegrityError:
            pass


class PessoaManager(ResolveFromSIEManager):
    sie_model_name = "PessoaSIE"

    def import_from_sie(self, pessoa):
        return self.create(
            pessoa_sie=pessoa,
            nome_pessoa=pessoa.nome_pessoa,
            cpf=pessoa.cpf,
            rg=pessoa.rg,
        )


class CentroManager(ResolveFromSIEManager):
    sie_model_name = "CentroSIE"

    def import_from_sie(self, centro):
        return self.create(
            centro_sie=centro,
            nome_centro=centro.nome_centro,
            sigla_centro=centro.sigla_centro,
            cod_estruturado=centro.cod_estruturado
        )


class UnidadeManager(ResolveFromSIEManager):
    sie_model_name = "UnidadeSIE"

    def import_from_sie(self, unidade):
        return self.create(
            unidade_sie=unidade,
            nome_unidade=unidade.nome_unidade,
            cod_estruturado=unidade.cod_estruturado,
            centro=unidade.centro,
            tipo_unidade=unidade.tipo_unidade,
            situacao_unidade=unidade.situacao_unidade
        )
