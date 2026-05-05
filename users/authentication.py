from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieOrHeaderJWTAuthentication(JWTAuthentication):
    """
    Extends SimpleJWT's built-in JWTAuthentication to support
    two token sources:

    1. Authorization header: "Bearer <token>"
       Used by: CLI, direct API calls, Postman
       
    2. access_token cookie (HTTP-only)
       Used by: Web portalned
       
    SimpleJWT's default only reads from the Authorization header.
    We override get_raw_token() to also check cookies.

    Why subclass instead of write from scratch?
    SimpleJWT's JWTAuthentication already handles:
    - Token decoding and validation
    - Expiry checking  
    - User lookup from token's user_id claim
    - Proper 401 error formatting
    We just need to add cookie support on top of that.
    """

    def authenticate(self, request):
        # First try the Authorization header (SimpleJWT's default behavior)
        header = self.get_header(request)

        if header is not None:
            # Header found — use SimpleJWT's standard flow
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token

        # No header — try the cookie (web portal flow)
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            # No token anywhere — return None (unauthenticated, not error)
            # DRF treats None as "anonymous user" not "invalid token"
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            # Bad cookie token — return None instead of raising
            # This allows the permission class to handle the 401
            return None

        return self.get_user(validated_token), validated_token

    def authenticate_header(self, request):
        # Tells clients what auth scheme to use in 401 responses
        return 'Bearer'