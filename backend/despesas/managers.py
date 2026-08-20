from django.core.exceptions import ValidationError
from django.db import models, transaction

from despesas.models import VersaoTransacao, Transacao


class TransacaoManager(models.Manager):
    def create_first_version(self, **kwargs):
        with transaction.atomic():
            transacao = Transacao.objects.create()
            first_version = VersaoTransacao.objects.create(**kwargs, transacao=transacao)
            transacao.versao_transacao = first_version
            transacao.save()
            return transacao

    def update_transacao_with_new_version(self, **kwargs):
        with transaction.atomic():
            try:
                transacao = Transacao.objects.get(id=kwargs['id_transacao'])
            except Transacao.DoesNotExist:
                raise ValidationError("Transação Inexistente.")

            all_versions = VersaoTransacao.objects.filter(transacao=transacao).order_by('-data_criacao')
            current_version = all_versions[0] if all_versions else None
            if not current_version:
                raise ValidationError("Transação inexistente.")

            new_version = VersaoTransacao.objects.create(
                transacao=transacao,
                numero_versao=current_version.numero_versao + 1,
                finalidade=current_version.finalidade,
                unidade_executora=current_version.unidade_executora,
                unidade_credora=current_version.unidade_credora,
                credito=current_version.credito,
                status_pagamento=kwargs[
                    'status_pagamento'] if 'status_pagamento' in kwargs else current_version.status_pagamento,
                beneficiario=kwargs['beneficiario'] if 'beneficiario' in kwargs else current_version.beneficiario,
                montante=kwargs['montante'] if 'montante' in kwargs else current_version.montante,
            )

            transacao.versao_transacao = new_version
            transacao.save()
            return transacao
