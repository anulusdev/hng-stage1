import requests as http_requests
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


def get_github_credentials(client_type: str) -> tuple[str, str, str]:
    """
    Returns (client_id, client_secret, callback_url) based on
    whether the request is coming from the web browser or the CLI.

    We have separate GitHub OAuth Apps for web and CLI because
    GitHub requires the callback URL to match exactly — localhost:8888
    for CLI and 127.0.0.1:8000 for web cannot share one OAuth App.
    """
    if client_type == 'cli':
        return (
            settings.GITHUB_CLI_CLIENT_ID,
            settings.GITHUB_CLI_CLIENT_SECRET,
            settings.GITHUB_CLI_CALLBACK_URL,
        )
    return (
        settings.GITHUB_WEB_CLIENT_ID,
        settings.GITHUB_WEB_CLIENT_SECRET,
        settings.GITHUB_WEB_CALLBACK_URL,
    )


def exchange_github_code(
    code: str,
    code_verifier: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> str | None:
    """
    Exchanges the GitHub authorization code for a GitHub access token.

    This is Step 2 of the OAuth flow:
    Step 1 — User clicks login, we redirect to GitHub
    Step 2 — GitHub redirects back with a code, we exchange it HERE
    Step 3 — We use the GitHub token to get user info

    code_verifier is the PKCE secret — GitHub checks that it matches
    the code_challenge we sent in Step 1, proving we started the flow.
    """
    response = http_requests.post(
        'https://github.com/login/oauth/access_token',
        headers={'Accept': 'application/json'},
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier,
        },
        timeout=10,
    )

    if response.status_code != 200:
        return None

    data = response.json()
    if 'error' in data:
        return None

    return data.get('access_token')


def get_github_user_info(github_token: str) -> dict | None:
    """
    Uses a GitHub access token to fetch the authenticated user's profile.

    Returns dict with: github_id, username, email, avatar_url
    
    Note: GitHub users can hide their email. If the main profile
    endpoint returns no email, we call the emails endpoint separately
    to find the primary email.
    """
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
    }

    resp = http_requests.get(
        'https://api.github.com/user',
        headers=headers,
        timeout=10,
    )

    if resp.status_code != 200:
        return None

    data = resp.json()
    email = data.get('email') or ''

    # If email is hidden on profile, fetch from emails endpoint
    if not email:
        emails_resp = http_requests.get(
            'https://api.github.com/user/emails',
            headers=headers,
            timeout=10,
        )
        if emails_resp.status_code == 200:
            emails = emails_resp.json()
            primary = next(
                (e['email'] for e in emails if e.get('primary')),
                ''
            )
            email = primary

    return {
        'github_id': str(data['id']),
        'username': data.get('login', ''),
        'email': email,
        'avatar_url': data.get('avatar_url', ''),
    }


def get_or_create_user(github_info: dict) -> User:
    """
    Creates a new user or updates an existing one based on github_id.

    Why github_id and not email or username?
    GitHub numeric IDs never change. Usernames and emails can be
    changed by the user at any time. Using github_id as the unique
    lookup key means we correctly identify returning users even
    if they renamed their GitHub account.

    Why update on every login?
    Username/avatar could have changed since last login.
    We keep our local copy in sync automatically.
    """
    user, created = User.objects.get_or_create(
        github_id=github_info['github_id'],
        defaults={
            'username': github_info['username'],
            'email': github_info['email'],
            'avatar_url': github_info['avatar_url'],
            'role': 'analyst',
        }
    )

    if not created:
        # Update potentially stale profile info
        user.username = github_info['username']
        user.email = github_info['email']
        user.avatar_url = github_info['avatar_url']

    user.last_login_at = timezone.now()
    user.save()

    return user


def issue_simplejwt_tokens(user: User) -> tuple[str, str]:
    """
    Uses SimpleJWT's RefreshToken class to generate a token pair.

    RefreshToken.for_user(user) is SimpleJWT's official API for
    creating tokens. It:
    1. Creates a RefreshToken signed with your SECRET_KEY
    2. Derives an AccessToken from it
    3. Embeds the user's primary key as the 'user_id' claim
    4. Respects ACCESS_TOKEN_LIFETIME and REFRESH_TOKEN_LIFETIME from settings
    5. Automatically handles the token_blacklist outstanding tokens table

    Returns (access_token_str, refresh_token_str)
    """
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    return str(access), str(refresh)