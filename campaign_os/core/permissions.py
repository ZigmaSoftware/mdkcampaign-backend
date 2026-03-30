"""
Screen-level CRUD permission enforcement for DRF viewsets.

Usage:
    class VoterViewSet(viewsets.ModelViewSet):
        permission_classes = [IsAuthenticated, ScreenPermission]
        screen_slug = 'voter'

How it works:
  - Reads the `screen_slug` attribute from the view.
  - Looks up UserScreenPermission for the current user's role + that slug.
  - Maps DRF action names to CRUD flags:
      list / retrieve            → can_view
      create                     → can_add
      update / partial_update    → can_edit
      destroy                    → can_delete
      (other custom actions)     → can_view  (safe default)
  - Admin role always passes.
  - If no `screen_slug` is set on the view, the check is skipped (pass-through).
"""
from rest_framework.permissions import BasePermission

# DRF action → CRUD flag name
ACTION_TO_FLAG = {
    'list':            'can_view',
    'retrieve':        'can_view',
    'create':          'can_add',
    'update':          'can_edit',
    'partial_update':  'can_edit',
    'destroy':         'can_delete',
}


class ScreenPermission(BasePermission):
    """
    Enforces UserScreenPermission for a viewset's declared `screen_slug`.
    """
    message = "You do not have permission to perform this action on this screen."

    def has_permission(self, request, view):
        # Must be authenticated first
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin role bypasses all screen checks
        if request.user.role == 'admin':
            return True

        screen_slug = getattr(view, 'screen_slug', None)
        if not screen_slug:
            # No screen defined — let through (backward compat)
            return True

        # Determine which CRUD flag to check
        action = getattr(view, 'action', None)
        flag = ACTION_TO_FLAG.get(action, 'can_view')

        # Look up the permission record
        from campaign_os.accounts.models import UserScreenPermission
        try:
            perm = UserScreenPermission.objects.get(
                role=request.user.role,
                user_screen__slug=screen_slug,
            )
            return getattr(perm, flag, False)
        except UserScreenPermission.DoesNotExist:
            return False
