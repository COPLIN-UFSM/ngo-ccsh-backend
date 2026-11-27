from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from entidades.managers import import_sie_contacts
from entidades.models import EmailSIE, Pessoa, PessoaSIE, Servidor, TelefoneSIE

BATCH_SIZE = 500


class Command(BaseCommand):
    help = "Importa pessoas e contatos dos servidores ativos no SIE."

    def handle(self, *args, **options):
        pessoa_sie_ids = sorted(
            set(
                Servidor._base_manager.filter(ativo=True)
                .values_list("pessoa_id", flat=True)
                .distinct()
            )
        )
        counts = {
            "people_created": 0,
            "people_existing": 0,
            "people_missing_in_sie": 0,
            "people_conflicts": 0,
            "emails_created": 0,
            "email_conflicts": 0,
            "invalid_emails": 0,
            "telefones_created": 0,
            "invalid_telefones": 0,
        }

        for offset in range(0, len(pessoa_sie_ids), BATCH_SIZE):
            batch_ids = pessoa_sie_ids[offset : offset + BATCH_SIZE]
            source_people = list(
                PessoaSIE._base_manager.filter(pk__in=batch_ids).order_by("pk")
            )
            people_by_sie_id = {pessoa.pk: pessoa for pessoa in source_people}
            counts["people_missing_in_sie"] += len(
                set(batch_ids) - set(people_by_sie_id)
            )

            email_values = defaultdict(list)
            for pessoa_sie_id, email in EmailSIE._base_manager.filter(
                pessoa_sie_id__in=people_by_sie_id
            ).values_list("pessoa_sie_id", "email"):
                email_values[pessoa_sie_id].append(email)

            telefone_values = defaultdict(list)
            for pessoa_sie_id, telefone in TelefoneSIE._base_manager.filter(
                pessoa_sie_id__in=people_by_sie_id
            ).values_list("pessoa_sie_id", "telefone"):
                telefone_values[pessoa_sie_id].append(telefone)

            existing_people = {
                pessoa.pessoa_sie_id: pessoa
                for pessoa in Pessoa._base_manager.filter(
                    pessoa_sie_id__in=people_by_sie_id
                )
            }

            for pessoa_sie in source_people:
                created = False
                with transaction.atomic():
                    pessoa = existing_people.get(pessoa_sie.pk)
                    if pessoa is None:
                        try:
                            with transaction.atomic():
                                pessoa = Pessoa._base_manager.create(
                                    pessoa_sie=pessoa_sie,
                                    nome_pessoa=pessoa_sie.nome_pessoa,
                                    cpf=pessoa_sie.cpf,
                                    rg=pessoa_sie.rg,
                                )
                            created = True
                        except IntegrityError:
                            pessoa = Pessoa._base_manager.filter(
                                pessoa_sie_id=pessoa_sie.pk
                            ).first()
                            if pessoa is None:
                                identity_conflict = (
                                    Pessoa._base_manager.filter(
                                        cpf=pessoa_sie.cpf
                                    ).exists()
                                    or Pessoa._base_manager.filter(
                                        rg=pessoa_sie.rg
                                    ).exists()
                                )
                                if not identity_conflict:
                                    raise
                                counts["people_conflicts"] += 1
                                continue

                    contact_counts = import_sie_contacts(
                        pessoa,
                        pessoa_sie,
                        emails=email_values[pessoa_sie.pk],
                        telefones=telefone_values[pessoa_sie.pk],
                    )

                    if created:
                        counts["people_created"] += 1
                    else:
                        counts["people_existing"] += 1
                    for key, value in contact_counts.items():
                        counts[key] += value

        self.stdout.write(
            self.style.SUCCESS(
                "Importação concluída. "
                f"Pessoas criadas: {counts['people_created']}; "
                f"pessoas já existentes: {counts['people_existing']}; "
                f"emails adicionados: {counts['emails_created']}; "
                f"telefones adicionados: {counts['telefones_created']}."
            )
        )

        skipped = (
            counts["people_missing_in_sie"]
            + counts["people_conflicts"]
            + counts["email_conflicts"]
            + counts["invalid_emails"]
            + counts["invalid_telefones"]
        )
        if skipped:
            self.stderr.write(
                self.style.WARNING(
                    "Registros ignorados ou conflitantes. "
                    f"Sem pessoa em v_sie_pessoas: "
                    f"{counts['people_missing_in_sie']}; "
                    f"conflitos de pessoa: {counts['people_conflicts']}; "
                    f"conflitos de email: {counts['email_conflicts']}; "
                    f"emails inválidos: {counts['invalid_emails']}; "
                    f"telefones inválidos: {counts['invalid_telefones']}."
                )
            )
