import hashlib
import base64
import secrets

from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .authentication import CookieOrHeaderJWTAuthentication
from .permissions import IsActiveUser, IsAnalystOrAdmin
from .services import (
    get_github_credentials,
    exchange_github_code,
    get_github_user_info,
    get_or_create_user,
    issue_simplejwt_tokens,
)


def set_auth_cookies(response, access_token: str, refresh_token: str):
    """
    Attaches both tokens as HTTP-only cookies to the response.

    httponly=True  → JavaScript cannot read these via document.cookie
    secure=False   → allow HTTP in local dev; True in production (HTTPS only)
    samesite='Lax' → sent on same-site requests and top-level navigations
                     but not on cross-site subrequests → CSRF protection
    """
    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite='Lax',
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite='Lax',
    )
    return response


@method_decorator(csrf_exempt, name='dispatch')
class GitHubLoginView(View):
    """
    Entry point for OAuth flow.

    Generates a state (CSRF protection for OAuth) and optionally
    accepts a code_challenge from the CLI (PKCE).

    The state is stored in the Django session and validated
    in the callback to prevent CSRF attacks on the OAuth flow itself.
    """

    def get(self, request):
        client_type = request.GET.get('client', 'web')
        client_id, _, redirect_uri = get_github_credentials(client_type)

        # state: random string to tie the callback to this request
        # If an attacker forges a callback, the state won't match
        state = secrets.token_urlsafe(32)

        # code_challenge: sent by CLI as part of PKCE
        # Web browser flow sends it too for consistency
        code_challenge = request.GET.get('code_challenge', '')

        # Store in session so callback can validate
        request.session['oauth_state'] = state
        request.session['oauth_client_type'] = client_type
        request.session.save()

        # Build the GitHub OAuth URL
        github_auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=user:email"
            f"&state={state}"
        )

        if code_challenge:
            github_auth_url += (
                f"&code_challenge={code_challenge}"
                f"&code_challenge_method=S256"
            )

        return redirect(github_auth_url)


@method_decorator(csrf_exempt, name='dispatch')
class GitHubCallbackView(View):
    def get(self, request):
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        code_verifier = request.GET.get('code_verifier', '')
        
        # The CLI will explicitly send client_type='cli'. 
        # If missing, we assume it's the web browser.
        client_type = request.GET.get('client_type') 
        if not client_type:
            client_type = request.session.get('oauth_client_type', 'web')

        if error:
            return JsonResponse({'status': 'error', 'message': 'GitHub OAuth was denied'}, status=400)

        # IMPORTANT: Only validate Django session state for Web. 
        # The CLI validates its own state locally before calling this endpoint.
        if client_type == 'web':
            session_state = request.session.get('oauth_state')
            if not state or state != session_state:
                return JsonResponse({'status': 'error', 'message': 'Invalid OAuth state parameter'}, status=400)

        client_id, client_secret, redirect_uri = get_github_credentials(client_type)

        github_token = exchange_github_code(code, code_verifier, client_id, client_secret, redirect_uri)
        if not github_token:
            return JsonResponse({'status': 'error', 'message': 'Failed to exchange code'}, status=502)

        github_info = get_github_user_info(github_token)
        user = get_or_create_user(github_info)
        
        if not user.is_active:
            return JsonResponse({'status': 'error', 'message': 'Account deactivated'}, status=403)

        access_token, refresh_token = issue_simplejwt_tokens(user)

        if client_type == 'cli':
            return JsonResponse({
                'status': 'success',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {'username': user.username, 'email': user.email, 'role': user.role}
            })

        response = redirect(f"{settings.FRONTEND_URL}/dashboard")
        return set_auth_cookies(response, access_token, refresh_token)


@method_decorator(csrf_exempt, name='dispatch')
class TokenRefreshView(View):
    """
    Implements SimpleJWT token rotation.

    When called:
    1. Reads the refresh token from cookie (web) or JSON body (CLI)
    2. Passes it to SimpleJWT's RefreshToken() class
    3. SimpleJWT validates it, blacklists it, and generates a new pair
    4. New tokens returned via cookie (web) or JSON (CLI)

    This uses SimpleJWT's built-in rotation — we don't manually
    delete tokens. BLACKLIST_AFTER_ROTATION in settings handles it.
    """

    def post(self, request):
        import json

        # Read refresh token from cookie first, then JSON body
        refresh_token_str = request.COOKIES.get('refresh_token')

        if not refresh_token_str:
            try:
                body = json.loads(request.body)
                refresh_token_str = body.get('refresh_token')
            except (json.JSONDecodeError, AttributeError):
                pass

        if not refresh_token_str:
            return JsonResponse(
                {'status': 'error', 'message': 'Refresh token is required'},
                status=400
            )

        try:
            # This is the SimpleJWT way to rotate tokens
            # RefreshToken() validates the token and checks the blacklist
            # Calling .blacklist() explicitly invalidates this token
            # Then we generate a new pair
            old_token = RefreshToken(refresh_token_str)

            # If ROTATE_REFRESH_TOKENS=True and BLACKLIST_AFTER_ROTATION=True,
            # SimpleJWT handles blacklisting automatically when we call
            # access_token = old_token.access_token
            # But we do it explicitly here for clarity
            old_token.blacklist()

            # Get the user from the old token's claims
            user_id = old_token['user_id']
            user = User.objects.get(id=user_id)

            if not user.is_active:
                return JsonResponse(
                    {'status': 'error', 'message': 'Account is deactivated'},
                    status=403
                )

            # Issue fresh token pair
            new_access, new_refresh = issue_simplejwt_tokens(user)

        except TokenError as e:
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid or expired refresh token'},
                status=401
            )
        except User.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'message': 'User not found'},
                status=401
            )

        # Return based on how the request came in
        if request.COOKIES.get('refresh_token'):
            response = JsonResponse({
                'status': 'success',
                'access_token': new_access,
                'refresh_token': new_refresh,
            })
            return set_auth_cookies(response, new_access, new_refresh)

        return JsonResponse({
            'status': 'success',
            'access_token': new_access,
            'refresh_token': new_refresh,
        })


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    """
    Blacklists the refresh token so it can never be used again.

    The access token will naturally expire in 3 minutes — we cannot
    invalidate it server-side because JWTs are stateless by nature.
    This is an accepted trade-off in JWT architecture: short-lived
    access tokens + blacklisted refresh tokens = effective logout.
    """

    def post(self, request):
        import json

        refresh_token_str = request.COOKIES.get('refresh_token')

        if not refresh_token_str:
            try:
                body = json.loads(request.body)
                refresh_token_str = body.get('refresh_token')
            except (json.JSONDecodeError, AttributeError):
                pass

        if refresh_token_str:
            try:
                token = RefreshToken(refresh_token_str)
                token.blacklist()
            except TokenError:
                # Already expired or invalid — that's fine, still log out
                pass

        response = JsonResponse({
            'status': 'success',
            'message': 'Logged out successfully'
        })

        # Clear cookies for web portal
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response


class WhoAmIView(APIView):
    """
    Protected endpoint — requires valid access token.
    Used by CLI's `insighta whoami` command and web portal account page.
    """
    authentication_classes = [CookieOrHeaderJWTAuthentication]
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request):
        user = request.user
        return Response({
            'status': 'success',
            'data': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'avatar_url': user.avatar_url,
                'last_login_at': (
                    user.last_login_at.strftime('%Y-%m-%dT%H:%M:%SZ')
                    if user.last_login_at else None
                ),
                'created_at': user.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            }
        })
