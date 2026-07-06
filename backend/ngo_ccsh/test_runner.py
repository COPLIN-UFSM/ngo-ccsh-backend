from django.test.runner import DiscoverRunner
from django.apps import apps
from django.db import connection


class CustomTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        old_config = super().setup_databases(**kwargs)

        with connection.schema_editor() as schema_editor:
            for model in apps.get_models():
                if not model._meta.managed:
                    original = model._meta.managed
                    model._meta.managed = True
                    try:
                        schema_editor.create_model(model)
                    except Exception:
                        pass
                    finally:
                        model._meta.managed = original

        return old_config