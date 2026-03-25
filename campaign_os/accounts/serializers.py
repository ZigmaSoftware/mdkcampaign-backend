"""
Serializers for authentication and user management
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from campaign_os.accounts.models import User, Role, UserLog, PagePermission


class UserSimpleSerializer(serializers.ModelSerializer):
    """Minimal user info - used in nested contexts"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'phone', 'role', 'role_display']


class UserDetailSerializer(serializers.ModelSerializer):
    """Full user details with hierarchical access info"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    constituency_name = serializers.CharField(source='constituency.name', read_only=True)
    booth_name = serializers.CharField(source='booth.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'full_name',
            'role', 'role_display',
            'state', 'state_name', 'district', 'district_name',
            'constituency', 'constituency_name', 'booth', 'booth_name',
            'profile_photo', 'bio', 'is_verified', 'is_active',
            'last_login_at', 'date_joined'
        ]
        read_only_fields = ['id', 'last_login_at', 'date_joined']


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating users"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'phone', 'first_name', 'last_name',
            'password', 'password_confirm',
            'role', 'state', 'district', 'constituency', 'booth',
            'profile_photo', 'bio'
        ]
    
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
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
