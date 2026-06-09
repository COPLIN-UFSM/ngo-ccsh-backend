from rest_framework.views import exception_handler
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # Verifica se a exceção resultou em um erro 404
    if response is not None and response.status_code == status.HTTP_404_NOT_FOUND:
        view = context.get('view')
        model_name = "Registro"
        
        if view and hasattr(view, 'get_queryset'):
            try:
                queryset = view.get_queryset()
                model_name = queryset.model._meta.verbose_name.title()
            except Exception:
                pass

        response.data = {
            "detail": f"{model_name} não encontrado."
        }

    return response
