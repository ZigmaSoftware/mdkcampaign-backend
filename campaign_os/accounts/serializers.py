"""
Serializers for authentication and user management
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from campaign_os.accounts.models import (
    User, Role, UserLog, PagePermission,
    MainScreen, UserScreen, UserScreenPermission,
)
from campaign_os.masters.models import VolunteerRole


class UserSimpleSerializer(serializers.ModelSerializer):
    """Minimal user info - used in nested contexts"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    volunteer_role = serializers.SerializerMethodField()
    volunteer_role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'phone', 'role', 'role_display', 'volunteer_role', 'volunteer_role_name']

    def get_volunteer_role(self, obj):
        volunteer_profile = getattr(obj, 'volunteer_profile', None)
        return getattr(volunteer_profile, 'volunteer_role_id', None)

    def get_volunteer_role_name(self, obj):
        volunteer_profile = getattr(obj, 'volunteer_profile', None)
        volunteer_role = getattr(volunteer_profile, 'volunteer_role', None)
        return getattr(volunteer_role, 'name', '')


class UserDetailSerializer(serializers.ModelSerializer):
    """Full user details with hierarchical access info"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    constituency_name = serializers.CharField(source='constituency.name', read_only=True)
    booth_name = serializers.CharField(source='booth.name', read_only=True)
    volunteer_role = serializers.SerializerMethodField()
    volunteer_role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'full_name',
            'role', 'role_display',
            'volunteer_role', 'volunteer_role_name',
            'state', 'state_name', 'district', 'district_name',
            'constituency', 'constituency_name', 'booth', 'booth_name',
            'profile_photo', 'bio', 'is_verified', 'is_active',
            'last_login_at', 'date_joined'
        ]
        read_only_fields = ['id', 'last_login_at', 'date_joined']

    def get_volunteer_role(self, obj):
        volunteer_profile = getattr(obj, 'volunteer_profile', None)
        return getattr(volunteer_profile, 'volunteer_role_id', None)

    def get_volunteer_role_name(self, obj):
        volunteer_profile = getattr(obj, 'volunteer_profile', None)
        volunteer_role = getattr(volunteer_profile, 'volunteer_role', None)
        return getattr(volunteer_role, 'name', '')


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating users"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    volunteer_role = serializers.PrimaryKeyRelatedField(
        queryset=VolunteerRole.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'phone', 'first_name', 'last_name',
            'password', 'password_confirm',
            'role', 'volunteer_role', 'state', 'district', 'constituency', 'booth',
            'profile_photo', 'bio'
        ]

    @staticmethod
    def _normalize_optional_strings(attrs):
        for field in ['phone', 'email', 'first_name', 'last_name']:
            if field in attrs and isinstance(attrs[field], str):
                attrs[field] = attrs[field].strip()
        if attrs.get('phone') == '':
            attrs['phone'] = None
        if attrs.get('email') == '':
            attrs['email'] = ''
        return attrs
    
    def validate(self, attrs):
        attrs = self._normalize_optional_strings(attrs)
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        if attrs.get('volunteer_role') is not None:
            attrs['role'] = 'volunteer'
        return attrs

    @staticmethod
    def _sync_volunteer_profile(user, volunteer_role):
        from campaign_os.volunteers.models import Volunteer

        full_name = (user.get_full_name() or user.username).strip()
        volunteer, _ = Volunteer.objects.get_or_create(
            user=user,
            defaults={
                'name': full_name,
                'phone': user.phone,
                'role': volunteer_role.name if volunteer_role else '',
                'volunteer_role': volunteer_role,
                'status': 'active',
            }
        )
        volunteer.name = full_name
        volunteer.phone = user.phone
        volunteer.role = volunteer_role.name if volunteer_role else ''
        volunteer.volunteer_role = volunteer_role
        volunteer.save()
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        volunteer_role = validated_data.pop('volunteer_role', None)
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        if volunteer_role is not None:
            self._sync_volunteer_profile(user, volunteer_role)
        return user
    
    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        volunteer_role = validated_data.pop('volunteer_role', serializers.empty)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()

        if volunteer_role is not serializers.empty:
            instance.role = 'volunteer'
            instance.save(update_fields=['role'])
            self._sync_volunteer_profile(instance, volunteer_role)
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional user info"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'phone': getattr(user, 'phone', None),
        }
        return data


class TokenRefreshSerializer(serializers.Serializer):
    """Refresh JWT token"""
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """Change user password"""
    old_password = serializers.CharField(write_only=True, min_length=8)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match'})
        return attrs


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role"""
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'created_at', 'updated_at']


class UserLogSerializer(serializers.ModelSerializer):
    """Serializer for user activity logs"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = UserLog
        fields = [
            'id', 'user', 'user_name', 'action', 'resource_type', 'resource_id',
            'details', 'ip_address', 'created_at'
        ]
        read_only_fields = fields


class PagePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagePermission
        fields = ['id', 'role', 'page_id', 'can_access']


class UserScreenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserScreen
        fields = ['id', 'main_screen', 'name', 'slug', 'icon', 'order', 'is_active']


class MainScreenSerializer(serializers.ModelSerializer):
    screens = UserScreenSerializer(many=True, read_only=True)

    class Meta:
        model = MainScreen
        fields = ['id', 'name', 'slug', 'icon', 'order', 'is_active', 'screens']


class UserScreenPermissionSerializer(serializers.ModelSerializer):
    user_screen_slug     = serializers.CharField(source='user_screen.slug', read_only=True)
    main_screen_slug     = serializers.CharField(source='user_screen.main_screen.slug', read_only=True)
    user_screen_name     = serializers.CharField(source='user_screen.name', read_only=True)
    main_screen_name     = serializers.CharField(source='user_screen.main_screen.name', read_only=True)
    allowed_actions      = serializers.ListField(read_only=True)

    class Meta:
        model = UserScreenPermission
        fields = [
            'id', 'role', 'user_screen', 'user_screen_slug', 'user_screen_name',
            'main_screen_slug', 'main_screen_name',
            'can_view', 'can_add', 'can_edit', 'can_delete', 'allowed_actions',
        ]
