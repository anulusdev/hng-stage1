import time
import logging

logger = logging.getLogger(__name__)


class APIVersionMiddleware:
    """
    Intercepts every /api/* request and checks for the
    X-API-Version: 1 header. Rejects without it.

    Why middleware and not a permission?
    Permissions run per-view. Middleware runs on every
    single request before routing — cleaner for a
    cross-cutting concern like versioning.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            version = request.headers.get('X-API-Version')
            if version != '1':
                from django.http import JsonResponse
                return JsonResponse(
                    {
                        'status': 'error',
                        'message': 'API version header required'
                    },
                    status=400
                )
        return self.get_response(request)


class RequestLoggingMiddleware:
    """
    Logs every request with method, path, status code,
    and how long it took to process.

    This runs after the view has processed — response is
    already generated when we log.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            '%s %s → %s (%.1fms)',
            request.method,
            request.path,
            response.status_code,
            duration_ms
        )

        return response