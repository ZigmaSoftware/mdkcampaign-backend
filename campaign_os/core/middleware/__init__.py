"""
JWT Authentication Middleware
"""
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTAuthMiddleware:
    """
    Middleware to extract JWT token from headers and set user context
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        return self.get_response(request)
