from django.apps import apps
from django.db import connection
from django.test.runner import DiscoverRunner


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
                    except AttributeError:
                        pass
                    finally:
                        model._meta.managed = original

        return old_config
