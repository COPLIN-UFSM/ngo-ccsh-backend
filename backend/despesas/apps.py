from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    name = "despesas"

    def ready(self):
        for model in self.get_models():
            if model.__name__.startswith("Historical"):
                model._meta.managed = False
