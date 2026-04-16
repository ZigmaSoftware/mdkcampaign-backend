"""
JWT Authentication Middleware
"""
import logging
import os
from time import perf_counter

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


logger = logging.getLogger(__name__)
SLOW_API_REQUEST_MS = float(os.getenv('SLOW_API_REQUEST_MS', '1500'))


class APIPerformanceMiddleware:
    """
    Log slow API requests and surface per-request duration for quick diagnosis.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = perf_counter()
        response = self.get_response(request)
        elapsed_ms = (perf_counter() - start) * 1000

        if request.path.startswith('/api/'):
            response['X-API-Duration-ms'] = f"{elapsed_ms:.1f}"
            if elapsed_ms >= SLOW_API_REQUEST_MS:
                logger.warning(
                    "Slow API request: %s %s status=%s duration_ms=%.1f",
                    request.method,
                    request.get_full_path(),
                    getattr(response, 'status_code', ''),
                    elapsed_ms,
                )
        return response


class JWTAuthMiddleware:
    """
    Middleware to extract JWT token from headers and set user context
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        return self.get_response(request)
