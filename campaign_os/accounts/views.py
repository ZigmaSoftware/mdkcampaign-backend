"""
Views for authentication and user management
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from campaign_os.core.permissions import (
    ScreenPermission,
    merge_screen_permissions,
    resolve_user_permission_roles,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Count, Q
from campaign_os.accounts.models import (
    User, Role, UserLog, PagePermission,
    MainScreen, UserScreen, UserScreenPermission,
)
from campaign_os.accounts.management.commands.seed_screens import (
    ensure_screen_catalog,
    seed_screen_permissions,
)
from campaign_os.accounts.serializers import (
    UserDetailSerializer, UserCreateUpdateSerializer, UserSimpleSerializer,
    CustomTokenObtainPairSerializer, ChangePasswordSerializer,
    RoleSerializer, UserLogSerializer, PagePermissionSerializer,
    MainScreenSerializer, UserScreenSerializer, UserScreenPermissionSerializer,
)


PERMISSION_MENU_LAYOUT = {
    'dashboard': [
        {
            'slug': 'dashboards',
            'name': 'Dashboards',
            'icon': 'ph ph-gauge',
            'screens': ['dashboard-home', 'activity-dashboard', 'task-dashboard'],
        },
    ],
    'entry': [
        {
            'slug': 'field-data',
            'name': 'Field Data',
            'icon': 'ph ph-database',
            'screens': ['voter', 'booth', 'family-mapping'],
        },
        {
            'slug': 'people',
            'name': 'People',
            'icon': 'ph ph-users-three',
            'screens': ['volunteer', 'beneficiary', 'user'],
        },
        {
            'slug': 'campaign',
            'name': 'Campaign',
            'icon': 'ph ph-megaphone',
            'screens': ['event', 'campaign'],
        },
        {
            'slug': 'activity',
            'name': 'Activity Logs',
            'icon': 'ph ph-clipboard-text',
            'screens': [
                'voter-survey',
                'field-activity',
                'attendance',
                'assign-telecalling',
                'telecalling-assigned',
                'feedback-review',
            ],
        },
    ],
    'masters-config': [
        {
            'slug': 'geography',
            'name': 'Geography',
            'icon': 'ph ph-globe-hemisphere-east',
            'screens': ['district', 'constituency', 'ward', 'area', 'booth-master', 'panchayat', 'union'],
        },
        {
            'slug': 'campaign-setup',
            'name': 'Campaign Setup',
            'icon': 'ph ph-megaphone',
            'screens': ['scheme', 'achievement', 'candidate', 'party', 'task-category', 'campaign-activity'],
        },
        {
            'slug': 'volunteer-setup',
            'name': 'Volunteer Setup',
            'icon': 'ph ph-identification-badge',
            'screens': ['volunteer-role', 'volunteer-type'],
        },
        {
            'slug': 'admin-security',
            'name': 'Admin & Security',
            'icon': 'ph ph-shield-check',
            'screens': ['user-mgmt', 'permissions'],
        },
    ],
    'report': [
        {
            'slug': 'reports',
            'name': 'Reports',
            'icon': 'ph ph-chart-bar',
            'screens': ['report-overview', 'voter-report', 'volunteer-report', 'campaign-report', 'activity-report'],
        },
    ],
    'opinion-poll': [
        {
            'slug': 'poll-management',
            'name': 'Poll Management',
            'icon': 'ph ph-megaphone',
            'screens': ['poll-questions', 'poll-results', 'poll-analysis'],
        },
    ],
}


def _permission_label(value: str) -> str:
    parts = [part for part in (value or '').replace('_', ' ').split() if part]
    return ' '.join(part.capitalize() for part in parts)


class LoginView(TokenObtainPairView):
    """
    User login endpoint
    Returns access and refresh tokens
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class TokenRefreshView(TokenRefreshView):
    """Refresh JWT token"""
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """
    User management viewset
    screen_slug = 'user'
    Endpoints:
        GET /api/v1/auth/users/ - List all users
        POST /api/v1/auth/users/ - Create new user
        GET /api/v1/auth/users/{id}/ - User details
        PUT /api/v1/auth/users/{id}/ - Update user
        DELETE /api/v1/auth/users/{id}/ - Delete user
        GET /api/v1/auth/users/me/ - Current user info
        POST /api/v1/auth/users/change-password/ - Change password
    """
    screen_slug = 'user'
    queryset = User.objects.filter(is_active=True).select_related(
        'state', 'district', 'constituency', 'booth', 'volunteer_profile__volunteer_role'
    )
    permission_classes = [IsAuthenticated, ScreenPermission]
    filterset_fields = ['role', 'state', 'district', 'constituency', 'booth']
    search_fields = ['username', 'first_name', 'last_name', 'phone', 'email', 'volunteer_profile__role', 'volunteer_profile__volunteer_role__name']

    def get_permissions(self):
        """
        Allow role-filtered user listing for task assignment without requiring
        the full user-management screen permission.
        """
        if self.action == 'list' and self.request.query_params.get('role') is not None:
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateUpdateSerializer
        return UserDetailSerializer

    @staticmethod
    def _normalize_role(value: str) -> str:
        return ' '.join((value or '').strip().lower().replace('_', ' ').replace('-', ' ').split())
    
    def get_queryset(self):
        """Filter users based on role and access level"""
        user = self.request.user
        base_qs = User.objects.filter(is_active=True).select_related(
            'state', 'district', 'constituency', 'booth', 'volunteer_profile__volunteer_role'
        )

        if user.is_staff or user.is_superuser:
            qs = base_qs
        elif user.role == 'admin':
            qs = base_qs
        elif user.role == 'district_head':
            qs = base_qs.filter(district=user.district)
        elif user.role == 'constituency_mgr':
            qs = base_qs.filter(constituency=user.constituency)
        else:
            qs = base_qs.filter(id=user.id)

        # /api/v1/auth/users/?role=<role>
        # Supports:
        # - internal role slug: booth_agent
        # - human label: Booth Agent
        # - volunteer-profile role text (for task assignment role filtering)
        role_param = self.request.query_params.get('role', '').strip()
        if role_param:
            role_norm = self._normalize_role(role_param)
            role_spaces = role_param.replace('_', ' ').replace('-', ' ')
            matching_role_codes = [
                code for code, label in User.ROLE_CHOICES
                if role_norm in {self._normalize_role(code), self._normalize_role(label)}
            ]

            qs = qs.filter(
                Q(role__in=matching_role_codes) |
                Q(volunteer_profile__role__iexact=role_param) |
                Q(volunteer_profile__role__iexact=role_spaces) |
                Q(volunteer_profile__volunteer_role__name__iexact=role_param) |
                Q(volunteer_profile__volunteer_role__name__iexact=role_spaces)
            ).distinct()

        return qs
    
    def create(self, request, *args, **kwargs):
        """Create new user - admin only"""
        if request.user.role not in ['admin', 'district_head']:
            return Response(
                {'detail': 'Only admins can create users'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail = UserDetailSerializer(serializer.instance).data
        return Response(detail, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        detail = UserDetailSerializer(serializer.instance).data
        return Response(detail)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current logged-in user details"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change current user password"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'detail': 'Password changed successfully'})
    
    @action(detail=False, methods=['POST'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Public user registration
        """
        serializer = UserCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'User registered successfully'},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def deactivate(self, request, pk=None):
        """Deactivate a user account"""
        user = self.get_object()
        if request.user.id != user.id and request.user.role != 'admin':
            return Response(
                {'detail': 'Cannot deactivate other users'},
                status=status.HTTP_403_FORBIDDEN
            )
        user.is_active = False
        user.save()
        return Response({'detail': 'User deactivated'})


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Role management (read-only for non-admins)
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


class UserLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit log viewer - admin only
    """
    queryset = UserLog.objects.all()
    serializer_class = UserLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'action', 'created_at']
    search_fields = ['action', 'resource_type']
    ordering_fields = ['created_at', 'action']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only admins can view logs"""
        if self.request.user.role != 'admin':
            return UserLog.objects.none()
        return super().get_queryset()


class PagePermissionViewSet(viewsets.ModelViewSet):
    """
    Manage page-level permissions per role.
    GET  /api/v1/auth/permissions/          — List all (filtered by role query param)
    PUT  /api/v1/auth/permissions/{id}/     — Update a permission (admin only)
    POST /api/v1/auth/permissions/seed/     — Seed defaults (admin only)
    GET  /api/v1/auth/permissions/my_access/ — Current user's allowed pages
    """
    queryset = PagePermission.objects.all()
    serializer_class = PagePermissionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'page_id', 'can_access']

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

    def update(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({'detail': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({'detail': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['POST'], url_path='seed')
    def seed(self, request):
        """Seed default permissions (admin only)"""
        if request.user.role != 'admin':
            return Response({'detail': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        from campaign_os.accounts.models import seed_default_permissions
        seed_default_permissions()
        return Response({'detail': 'Default permissions seeded'})

    @action(detail=False, methods=['GET'], url_path='my_access')
    def my_access(self, request):
        """
        Return the current user's page access list AND screen-level CRUD permissions.

        For volunteers the lookup key prefers their VolunteerRole master name,
        then volunteer_type slug, then falls back to the generic "volunteer".

        Response shape:
        {
          "role": "admin",
          "allowed_pages": ["dashboard", "entry", ...],
          "screen_permissions": {
            "entry": {
              "voter": ["view", "add", "edit", "delete"],
              "booth":  ["view"]
            },
            "masters-config": { ... }
          }
        }
        """
        seed_screen_permissions(overwrite_existing=False)

        roles = resolve_user_permission_roles(request.user)
        primary_role = roles[0] if roles else request.user.role

        perms = (
            UserScreenPermission.objects
            .filter(role__in=roles or [request.user.role])
            .select_related('user_screen__main_screen')
        )
        screen_permissions, allowed_main_screens = merge_screen_permissions(perms)

        return Response({
            'role': primary_role,
            'allowed_pages': allowed_main_screens,
            'screen_permissions': screen_permissions,
        })


class MainScreenViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List all main screens with their child user screens.
    GET /api/v1/auth/main-screens/
    """
    serializer_class = MainScreenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        ensure_screen_catalog()
        return MainScreen.objects.filter(is_active=True).prefetch_related('screens')


class UserScreenViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List all user (sub) screens, optionally filtered by main_screen slug.
    GET /api/v1/auth/user-screens/?main_screen=entry
    """
    queryset = UserScreen.objects.filter(is_active=True).select_related('main_screen')
    serializer_class = UserScreenSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['main_screen', 'is_active']

    def get_queryset(self):
        qs = super().get_queryset()
        ms_slug = self.request.query_params.get('main_screen')
        if ms_slug:
            qs = qs.filter(main_screen__slug=ms_slug)
        return qs


class UserScreenPermissionViewSet(viewsets.ModelViewSet):
    """
    Manage CRUD-level permissions per role per user screen.

    GET  /api/v1/auth/screen-permissions/             – list (filter by ?role=admin)
    PUT  /api/v1/auth/screen-permissions/{id}/        – update (admin only)
    POST /api/v1/auth/screen-permissions/seed/        – seed defaults (admin only)
    GET  /api/v1/auth/screen-permissions/by_role/     – grouped by main_screen for a role (?role=volunteer)
    """
    queryset = UserScreenPermission.objects.all().select_related('user_screen__main_screen')
    serializer_class = UserScreenPermissionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'user_screen']

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        ms_slug = self.request.query_params.get('main_screen')
        if role:
            qs = qs.filter(role=role)
        if ms_slug:
            qs = qs.filter(user_screen__main_screen__slug=ms_slug)
        return qs

    def _build_matrix_rows(self, role, main_screen_slug=None):
        ensure_screen_catalog()
        seed_screen_permissions(overwrite_existing=False)

        existing = {
            perm.user_screen_id: perm
            for perm in (
                UserScreenPermission.objects
                .filter(role=role)
                .select_related('user_screen__main_screen')
            )
        }

        screens = (
            UserScreen.objects
            .filter(is_active=True)
            .select_related('main_screen')
            .order_by('main_screen__order', 'order')
        )
        if main_screen_slug:
            screens = screens.filter(main_screen__slug=main_screen_slug)

        rows = []
        for screen in screens:
            perm = existing.get(screen.id)
            rows.append({
                'id': perm.id if perm else None,
                'role': role,
                'user_screen': screen.id,
                'user_screen_slug': screen.slug,
                'user_screen_name': screen.name,
                'main_screen_slug': screen.main_screen.slug,
                'main_screen_name': screen.main_screen.name,
                'can_view': perm.can_view if perm else False,
                'can_add': perm.can_add if perm else False,
                'can_edit': perm.can_edit if perm else False,
                'can_delete': perm.can_delete if perm else False,
                'allowed_actions': perm.allowed_actions if perm else [],
            })
        return rows

    def list(self, request, *args, **kwargs):
        role = request.query_params.get('role', '').strip()
        if role:
            return Response(self._build_matrix_rows(role, request.query_params.get('main_screen')))
        return super().list(request, *args, **kwargs)

    def _admin_only(self, request):
        if request.user.role != 'admin':
            from rest_framework.response import Response as R
            return R({'detail': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        err = self._admin_only(request)
        if err: return err
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        err = self._admin_only(request)
        if err: return err
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['POST'], url_path='seed')
    def seed(self, request):
        """Seed default screen permissions (admin only)"""
        if request.user.role != 'admin':
            return Response({'detail': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        seed_screen_permissions()
        return Response({'detail': 'Screen permissions seeded'})

    @action(detail=False, methods=['POST'], url_path='bulk-upsert')
    def bulk_upsert(self, request):
        """Create or update permission rows for a role in one request."""
        if request.user.role != 'admin':
            return Response({'detail': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

        role = (request.data.get('role') or '').strip()
        items = request.data.get('permissions') or []
        if not role:
            return Response({'detail': 'Role is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(items, list) or not items:
            return Response({'detail': 'permissions must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        updated = 0

        for item in items:
            screen = None
            screen_id = item.get('user_screen')
            screen_slug = (item.get('user_screen_slug') or '').strip()

            if screen_id:
                screen = UserScreen.objects.filter(id=screen_id, is_active=True).first()
            if not screen and screen_slug:
                screen = UserScreen.objects.filter(slug=screen_slug, is_active=True).first()
            if not screen:
                return Response(
                    {'detail': f'Unknown user screen: {screen_id or screen_slug}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            perm, was_created = UserScreenPermission.objects.update_or_create(
                role=role,
                user_screen=screen,
                defaults={
                    'can_view': bool(item.get('can_view')),
                    'can_add': bool(item.get('can_add')),
                    'can_edit': bool(item.get('can_edit')),
                    'can_delete': bool(item.get('can_delete')),
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response({
            'detail': 'Permissions saved',
            'created': created,
            'updated': updated,
        })

    @action(detail=False, methods=['GET'], url_path='catalog')
    def catalog(self, request):
        """
        Metadata for the user-permission builder UI.
        """
        from campaign_os.masters.models import VolunteerRole

        ensure_screen_catalog()

        volunteer_roles = (
            VolunteerRole.objects
            .filter(is_active=True)
            .annotate(user_count=Count('volunteers', filter=Q(volunteers__is_active=True), distinct=True))
            .order_by('order', 'name')
        )
        roles = [
            {
                'value': volunteer_role.name,
                'label': volunteer_role.name,
                'user_count': volunteer_role.user_count,
            }
            for volunteer_role in volunteer_roles
        ]

        permission_roles = set(
            UserScreenPermission.objects
            .values_list('role', flat=True)
            .distinct()
        )

        main_screens = (
            MainScreen.objects
            .filter(is_active=True)
            .prefetch_related('screens')
            .order_by('order')
        )

        menus = []
        for menu in main_screens:
            active_screens = sorted(
                [screen for screen in menu.screens.all() if screen.is_active],
                key=lambda screen: screen.order,
            )
            screen_map = {screen.slug: screen for screen in active_screens}
            submenus = []
            consumed = set()

            for group in PERMISSION_MENU_LAYOUT.get(menu.slug, []):
                items = []
                for slug in group['screens']:
                    screen = screen_map.get(slug)
                    if not screen:
                        continue
                    consumed.add(screen.slug)
                    items.append({
                        'id': screen.id,
                        'slug': screen.slug,
                        'name': screen.name,
                        'icon': screen.icon,
                    })

                if not items:
                    continue

                submenus.append({
                    'slug': group['slug'],
                    'name': group['name'],
                    'icon': group['icon'],
                    'screen_slugs': [item['slug'] for item in items],
                    'items': items,
                })

            for screen in active_screens:
                if screen.slug in consumed:
                    continue
                submenus.append({
                    'slug': screen.slug,
                    'name': screen.name,
                    'icon': screen.icon,
                    'screen_slugs': [screen.slug],
                    'items': [],
                })

            menus.append({
                'id': menu.id,
                'slug': menu.slug,
                'name': menu.name,
                'icon': menu.icon,
                'submenus': submenus,
            })

        return Response({
            'roles': roles,
            'permission_roles': sorted(permission_roles),
            'menus': menus,
        })

    @action(detail=False, methods=['GET'], url_path='by_role')
    def by_role(self, request):
        """
        Return permissions for a specific role grouped by main screen.
        ?role=volunteer  (defaults to current user's role)
        """
        role = request.query_params.get('role', request.user.role)
        # Only admin can query other roles
        if role != request.user.role and request.user.role != 'admin':
            return Response({'detail': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

        perms = (
            UserScreenPermission.objects
            .filter(role=role)
            .select_related('user_screen__main_screen')
        )
        grouped = {}
        for p in perms:
            ms = p.user_screen.main_screen
            ms_key = ms.slug
            if ms_key not in grouped:
                grouped[ms_key] = {
                    'id': ms.id,
                    'name': ms.name,
                    'slug': ms.slug,
                    'screens': [],
                }
            grouped[ms_key]['screens'].append({
                'id': p.id,
                'user_screen_id': p.user_screen.id,
                'slug': p.user_screen.slug,
                'name': p.user_screen.name,
                'icon': p.user_screen.icon,
                'can_view': p.can_view,
                'can_add': p.can_add,
                'can_edit': p.can_edit,
                'can_delete': p.can_delete,
                'allowed_actions': p.allowed_actions,
            })
        return Response({'role': role, 'main_screens': list(grouped.values())})
