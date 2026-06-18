from rest_framework.renderers import JSONRenderer
from rest_framework import status


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")

        if response and status.is_success(response.status_code):
            if isinstance(data, dict) and "status" in data:
                custom_data = data
            else:
                custom_data = {"status": "success", "message": "Operação realizada com sucesso.", "data": data}
        else:
            custom_data = {"status": "error", "message": "Ocorreu um erro na requisição.", "errors": data}

        return super().render(custom_data, accepted_media_type, renderer_context)
