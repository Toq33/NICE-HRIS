"""Serializers for Authentication, Users, Roles, and Permissions."""
from rest_framework import serializers

from .models import DataScope, LoginHistory, Role, RolePermission, User


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    default_company_name = serializers.CharField(source="default_company.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "full_name_bn",
            "phone",
            "tenant",
            "tenant_name",
            "default_company",
            "default_company_name",
            "experience_mode",
            "is_platform_admin",
            "can_view_salary",
            "can_view_medical",
            "has_approval_authority",
            "totp_enabled",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "tenant", "is_platform_admin", "created_at"]


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ["id", "module_number", "actions"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = RolePermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "code",
            "description",
            "is_system_role",
            "can_view_confidential_salary",
            "can_view_confidential_medical",
            "has_approval_authority",
            "permissions",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DataScopeSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = DataScope
        fields = [
            "id",
            "user",
            "user_email",
            "role",
            "role_name",
            "scope_type",
            "company_ids",
            "branch_ids",
            "department_ids",
        ]


class LoginHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginHistory
        fields = [
            "id",
            "email_attempted",
            "ip_address",
            "user_agent",
            "succeeded",
            "created_at",
        ]
