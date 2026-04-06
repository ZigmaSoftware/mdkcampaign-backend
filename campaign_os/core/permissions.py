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

ACTION_ORDER = ('view', 'add', 'edit', 'delete')


def _append_candidate(candidates, value):
    candidate = (value or '').strip()
    if candidate and candidate not in candidates:
        candidates.append(candidate)


def get_user_permission_roles(user):
    """
    Return all role keys that may grant screen permissions for this user.

    Volunteer users can inherit permissions from their VolunteerRole master
    name or volunteer_type in addition to the generic "volunteer" role.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return []

    role = (getattr(user, 'role', '') or '').strip()
    if role != 'volunteer':
        return [role] if role else []

    candidates = []

    try:
        from campaign_os.volunteers.models import Volunteer

        volunteer = (
            Volunteer.objects
            .filter(user=user)
            .select_related('volunteer_role')
            .first()
        )

        if volunteer and volunteer.volunteer_role and volunteer.volunteer_role.name:
            _append_candidate(candidates, volunteer.volunteer_role.name)

        if volunteer and volunteer.role:
            _append_candidate(candidates, volunteer.role)

        if volunteer and volunteer.volunteer_type:
            _append_candidate(candidates, volunteer.volunteer_type)
            _append_candidate(
                candidates,
                volunteer.volunteer_type.strip().lower().replace(' ', '_'),
            )
    except Exception:
        pass

    _append_candidate(candidates, 'volunteer')
    return candidates


def _role_has_screen_permissions(role, screen_slug=None):
    role_key = (role or '').strip()
    if not role_key:
        return False

    from campaign_os.accounts.models import UserScreenPermission

    queryset = UserScreenPermission.objects.filter(role=role_key)
    if screen_slug:
        queryset = queryset.filter(user_screen__slug=screen_slug)
    return queryset.exists()


def resolve_user_permission_roles(user, screen_slug=None):
    """
    Resolve the effective permission role(s) for the user.

    Volunteer users may have multiple candidate keys (VolunteerRole name,
    volunteer profile role, volunteer_type, generic volunteer). We only want
    one permission source at a time:
      1. first specific volunteer role that has matching permission rows
      2. generic "volunteer" fallback

    This keeps user-type-specific permissions from being widened by the
    generic volunteer role.
    """
    candidates = get_user_permission_roles(user)
    if not candidates:
        return []

    role = (getattr(user, 'role', '') or '').strip()
    if role != 'volunteer':
        return [candidates[0]]

    specific_candidates = [candidate for candidate in candidates if candidate != 'volunteer']

    for candidate in specific_candidates:
        if _role_has_screen_permissions(candidate, screen_slug=screen_slug):
            return [candidate]

    if _role_has_screen_permissions('volunteer', screen_slug=screen_slug) or 'volunteer' in candidates:
        return ['volunteer']

    return []


def merge_screen_permissions(permission_rows):
    """
    Merge permission rows into the frontend response shape.
    """
    screen_permissions = {}
    allowed_main_screens = {'dashboard'}

    for permission in permission_rows:
        actions = permission.allowed_actions
        if not actions:
            continue

        main_slug = permission.user_screen.main_screen.slug
        screen_slug = permission.user_screen.slug
        bucket = screen_permissions.setdefault(main_slug, {}).setdefault(screen_slug, set())
        bucket.update(actions)
        allowed_main_screens.add(main_slug)

    normalized_permissions = {}
    for main_slug, screens in screen_permissions.items():
        normalized_permissions[main_slug] = {}
        for screen_slug, actions in screens.items():
            normalized_permissions[main_slug][screen_slug] = [
                action for action in ACTION_ORDER if action in actions
            ]

    return normalized_permissions, list(allowed_main_screens)


def iter_view_permission_slugs(view, flag=None):
    """
    Return all screen slugs that can authorize the given view.

    Most views use a single `screen_slug`. A few compatibility paths, such as
    User Settings, may expose the same backend view under more than one
    permission slug.
    """
    slugs = []

    if flag == 'can_view':
        view_slugs = getattr(view, 'view_permission_screen_slugs', None) or ()
        for slug in view_slugs:
            normalized = (slug or '').strip()
            if normalized and normalized not in slugs:
                slugs.append(normalized)

    extra_slugs = getattr(view, 'permission_screen_slugs', None) or ()
    for slug in extra_slugs:
        normalized = (slug or '').strip()
        if normalized and normalized not in slugs:
            slugs.append(normalized)

    screen_slug = getattr(view, 'screen_slug', None)
    normalized_screen_slug = (screen_slug or '').strip() if isinstance(screen_slug, str) else screen_slug
    if normalized_screen_slug and normalized_screen_slug not in slugs:
        slugs.append(normalized_screen_slug)

    return slugs


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

        # Determine which CRUD flag to check
        action = getattr(view, 'action', None)
        flag = ACTION_TO_FLAG.get(action, 'can_view')
        screen_slugs = iter_view_permission_slugs(view, flag=flag)
        if not screen_slugs:
            # No screen defined — let through (backward compat)
            return True

        from campaign_os.accounts.models import UserScreenPermission

        for screen_slug in screen_slugs:
            roles = resolve_user_permission_roles(request.user, screen_slug=screen_slug)
            if not roles:
                continue

            permissions_qs = UserScreenPermission.objects.filter(
                role__in=roles,
                user_screen__slug=screen_slug,
            )
            if any(getattr(permission, flag, False) for permission in permissions_qs):
                return True

        return False
