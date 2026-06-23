from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response



class PaginationWithSize(PageNumberPagination):
    page_size = 10
    page_size_query_param = "quantidade"
    page_query_param = "pagina"
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(
            {
                # "status": "success",
                # "message": "Dados listados com sucesso.",
                "count": self.page.paginator.count,
                "prev": self.get_previous_link(),
                "next": self.get_next_link(),
                "data": data,
            }
        )
