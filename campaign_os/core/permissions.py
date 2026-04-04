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


def get_screen_permission_role_candidates(user):
    """
    Return role keys to try for screen permissions, in precedence order.

    Volunteer users can inherit permissions from either:
    - their VolunteerRole master name
    - their volunteer_type slug
    - the generic ``volunteer`` role
    """
    if not user or not user.is_authenticated:
        return []

    role = getattr(user, 'role', None)
    if role != 'volunteer':
        return [role] if role else []

    try:
        from campaign_os.volunteers.models import Volunteer

        volunteer = (
            Volunteer.objects
            .filter(user=user)
            .select_related('volunteer_role')
            .first()
        )

        role_candidates = []
        if volunteer and volunteer.volunteer_role and volunteer.volunteer_role.name:
            role_candidates.append(volunteer.volunteer_role.name.strip())
        if volunteer and volunteer.volunteer_type:
            role_candidates.append(
                volunteer.volunteer_type.strip().lower().replace(' ', '_')
            )
        role_candidates.append('volunteer')

        seen = set()
        deduped = []
        for candidate in role_candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            deduped.append(candidate)
        return deduped
    except Exception:
        return [role]

    return [role]


def resolve_screen_permission_role(user, screen_slug=None):
    """
    Resolve the effective role key used for a specific screen.

    For volunteers, role-specific permissions override generic volunteer
    permissions only when that specific role actually has a row for the screen.
    If not, authorization falls back to the next candidate role.
    """
    candidates = get_screen_permission_role_candidates(user)
    if not candidates:
        return None
    if not screen_slug:
        return candidates[0]

    try:
        from campaign_os.accounts.models import UserScreenPermission

        for candidate in candidates:
            if UserScreenPermission.objects.filter(
                role=candidate,
                user_screen__slug=screen_slug,
            ).exists():
                return candidate
    except Exception:
        pass

    return None


def get_effective_screen_permission(user, screen_slug):
    """
    Return the first matching permission row for a screen across all candidate
    permission roles.
    """
    resolved_role = resolve_screen_permission_role(user, screen_slug=screen_slug)
    if not resolved_role:
        return None

    try:
        from campaign_os.accounts.models import UserScreenPermission

        return (
            UserScreenPermission.objects
            .select_related('user_screen__main_screen')
            .filter(role=resolved_role, user_screen__slug=screen_slug)
            .first()
        )
    except Exception:
        return None


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

        perm = get_effective_screen_permission(request.user, screen_slug)
        if not perm:
            return False
        return getattr(perm, flag, False)
