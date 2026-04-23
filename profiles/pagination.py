from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ProfilePagination(PageNumberPagination):
    """
    Custom paginator that:
    - Uses 'limit' as the page size param (task requirement)
    - Caps at 50 results per page
    - Returns the task's required response format
    """
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 50
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'status': 'success',
            'page': self.page.number,
            'limit': self.get_page_size(self.request),
            'total': self.page.paginator.count,
            'data': data
        })

    def get_paginated_response_schema(self, schema):
        return {
            'status': 'success',
            'page': 'integer',
            'limit': 'integer',
            'total': 'integer',
            'data': schema
        }