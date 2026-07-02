from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Cria tabelas com managed=False (banco de desenvolvimento apenas)."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING("[INFO] Criando tabelas do banco de dados")
        )

        for model in apps.get_models():
            if model._meta.managed:
                continue

            original = model._meta.managed
            model._meta.managed = True

            try:
                with connection.schema_editor() as schema_editor:
                    schema_editor.create_model(model)

                self.stdout.write(self.style.SUCCESS(f"  [OK] {model._meta.db_table}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[ERRO] {model._meta.db_table}: {e}"))
            finally:
                model._meta.managed = original
