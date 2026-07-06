from django.db import models
from django.apps import apps
from django.db import IntegrityError, transaction


class ResolveFromSIEManager(models.Manager):
    """
    Importa objetos do SIE quando eles são requisitados pela primeira vez.

    Subclasses devem implementar:
        * sie_model_name
        * import_from_sie()
    """
    sie_model_name = None

    @property
    def sie_model(self):
        return apps.get_model("entidades", self.sie_model_name)

    def import_from_sie(self, sie_obj):
        raise NotImplementedError

    def resolve(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            pass

        try:
            sie = self.sie_model.objects.get(**kwargs)
        except self.sie_model.DoesNotExist:
            raise self.model.DoesNotExist

        try:
            with transaction.atomic():
                return self.import_from_sie(sie)

        except IntegrityError:
            return self.get(**kwargs)


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
