"""
Views for authentication and user management
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from campaign_os.core.permissions import ScreenPermission
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from campaign_os.accounts.models import (
    User, Role, UserLog, PagePermission,
    MainScreen, UserScreen, UserScreenPermission,
)
from campaign_os.accounts.serializers import (
    UserDetailSerializer, UserCreateUpdateSerializer, UserSimpleSerializer,
    CustomTokenObtainPairSerializer, ChangePasswordSerializer,
    RoleSerializer, UserLogSerializer, PagePermissionSerializer,
    MainScreenSerializer, UserScreenSerializer, UserScreenPermissionSerializer,
)


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
    queryset = User.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated, ScreenPermission]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateUpdateSerializer
        return UserDetailSerializer
    
    def get_queryset(self):
        """Filter users based on role and access level"""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return User.objects.all()
        if user.role == 'admin':
            return User.objects.all()
        if user.role == 'district_head':
            return User.objects.filter(district=user.district)
        if user.role == 'constituency_mgr':
            return User.objects.filter(constituency=user.constituency)
        return User.objects.filter(id=user.id)
    
    def create(self, request, *args, **kwargs):
        """Create new user - admin only"""
        if request.user.role not in ['admin', 'district_head']:
            return Response(
                {'detail': 'Only admins can create users'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
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

        For volunteers the lookup key is their volunteer_type slug
        (e.g. "party_worker") when one exists; otherwise falls back to "volunteer".

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
        role = request.user.role

        # For volunteer users, try to resolve their specific volunteer-type slug
        if role == 'volunteer':
            try:
                from campaign_os.volunteers.models import Volunteer
                vol = Volunteer.objects.filter(user=request.user).first()
                if vol and vol.volunteer_type:
                    vol_type_slug = vol.volunteer_type.strip().lower().replace(' ', '_')
                    if UserScreenPermission.objects.filter(role=vol_type_slug).exists():
                        role = vol_type_slug
            except Exception:
                pass  # Fall back to generic 'volunteer'

        # Build screen_permissions and derive allowed_pages from UserScreenPermission
        perms = (
            UserScreenPermission.objects
            .filter(role=role)
            .select_related('user_screen__main_screen')
        )
        screen_permissions = {}
        allowed_main_screens = set()

        for p in perms:
            actions = p.allowed_actions
            if actions:
                ms_slug = p.user_screen.main_screen.slug
                us_slug = p.user_screen.slug
                screen_permissions.setdefault(ms_slug, {})[us_slug] = actions
                allowed_main_screens.add(ms_slug)

        # Dashboard is always accessible (it has no UserScreen sub-entries)
        allowed_main_screens.add('dashboard')

        return Response({
            'role': role,
            'allowed_pages': list(allowed_main_screens),
            'screen_permissions': screen_permissions,
        })


class MainScreenViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List all main screens with their child user screens.
    GET /api/v1/auth/main-screens/
    """
    queryset = MainScreen.objects.filter(is_active=True).prefetch_related('screens')
    serializer_class = MainScreenSerializer
    permission_classes = [IsAuthenticated]


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
        from campaign_os.accounts.management.commands.seed_screens import seed_screen_permissions
        seed_screen_permissions()
        return Response({'detail': 'Screen permissions seeded'})

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
