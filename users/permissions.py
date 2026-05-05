from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    """
    Blocks inactive users (is_active=False) with 403.
    Applied alongside IsAuthenticated on all protected endpoints.

    Why separate from IsAuthenticated?
    IsAuthenticated only checks if a valid token exists.
    IsActiveUser checks if the account hasn't been deactivated
    after the token was issued. A user could have a valid token
    but be banned — IsAuthenticated alone wouldn't catch that.
    """
    message = {'status': 'error', 'message': 'Account has been deactivated'}

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_active', False)
        )


class IsAdminRole(BasePermission):
    """
    Allows only users with role='admin'.
    
    Used for: POST /api/profiles, DELETE /api/profiles/{id}
    
    Admins have full access — create, delete, query.
    """
    message = {'status': 'error', 'message': 'Admin role required'}

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'admin'
        )


class IsAnalystOrAdmin(BasePermission):
    """
    Allows both analysts and admins.
    
    Used for: all GET endpoints — read-only operations.
    
    Analysts are read-only users — they can query and search
    but cannot create or delete profiles.
    """
    message = {'status': 'error', 'message': 'Insufficient permissions'}

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) in ['admin', 'analyst']
        )