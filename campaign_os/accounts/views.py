"""
Views for authentication and user management
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from campaign_os.accounts.models import User, Role, UserLog, PagePermission
from campaign_os.accounts.serializers import (
    UserDetailSerializer, UserCreateUpdateSerializer, UserSimpleSerializer,
    CustomTokenObtainPairSerializer, ChangePasswordSerializer,
    RoleSerializer, UserLogSerializer, PagePermissionSerializer
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
    Endpoints:
        GET /api/v1/auth/users/ - List all users
        POST /api/v1/auth/users/ - Create new user
        GET /api/v1/auth/users/{id}/ - User details
        PUT /api/v1/auth/users/{id}/ - Update user
        DELETE /api/v1/auth/users/{id}/ - Delete user
        GET /api/v1/auth/users/me/ - Current user info
        POST /api/v1/auth/users/change-password/ - Change password
    """
    queryset = User.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    
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
        """Return list of page_ids the current user can access"""
        role = request.user.role
        allowed = list(
            PagePermission.objects.filter(role=role, can_access=True).values_list('page_id', flat=True)
        )
        return Response({'role': role, 'allowed_pages': allowed})
