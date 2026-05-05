import math
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class ProfilePagination(PageNumberPagination):
    """
    Custom paginator that:
    - Uses 'limit' as the page size param (task requirement)
    - Caps at 50 results per page
    - Returns the task's required response format including links and total_pages
    """
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 50
    page_query_param = 'page'

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        
        # Calculate total pages: e.g., 2026 / 10 = 202.6 -> rounds up to 203
        total_pages = math.ceil(total / limit) if limit else 1
        current_page = self.page.number

        # Helper function to generate relative URIs while preserving filters
        def get_url(page_num):
            if not page_num or page_num < 1 or page_num > total_pages:
                return None
            
            # request.GET contains all current filters (e.g., gender=male)
            # We copy it so we don't accidentally mutate the original request
            query_params = self.request.GET.copy()
            query_params['page'] = page_num
            query_params['limit'] = limit
            
            # Returns a string like: /api/profiles?gender=male&page=2&limit=10
            return f"{self.request.path}?{query_params.urlencode()}"

        return Response({
            'status': 'success',
            'page': current_page,
            'limit': limit,
            'total': total,
            'total_pages': total_pages,
            'links': {
                'self': get_url(current_page),
                'next': get_url(current_page + 1) if current_page < total_pages else None,
                'prev': get_url(current_page - 1) if current_page > 1 else None
            },
            'data': data
        })