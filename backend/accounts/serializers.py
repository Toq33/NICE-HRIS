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
    permissions = serializers.SerializerMethodField(read_only=True)
    code = serializers.SlugField(max_length=60, required=False, allow_blank=True)
    template_role_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "code",
            "badge_label",
            "description",
            "display_order",
            "is_system_role",
            "can_view_confidential_salary",
            "can_view_confidential_medical",
            "has_approval_authority",
            "template_role_code",
            "permissions",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_permissions(self, obj: Role) -> list[dict]:
        perms = RolePermission.unscoped_objects.filter(
            role=obj, deleted_at__isnull=True
        ).order_by("module_number")
        return RolePermissionSerializer(perms, many=True).data

    def create(self, validated_data):
        from django.utils.text import slugify

        from core.context import get_current_tenant_id, tenant_context
        from platform_admin.models import Tenant

        template_code = validated_data.pop("template_role_code", "")
        raw_code = validated_data.get("code") or slugify(validated_data.get("name", "custom-role"))
        base_code = raw_code[:50] or "custom-role"
        code = base_code
        idx = 2
        while Role.objects.filter(code=code).exists():
            code = f"{base_code}-{idx}"
            idx += 1
        validated_data["code"] = code
        if not validated_data.get("badge_label"):
            validated_data["badge_label"] = "Custom Role"

        active_tenant = None
        current_tid = get_current_tenant_id()
        if current_tid:
            active_tenant = Tenant.objects.filter(pk=current_tid).first()
        if not active_tenant:
            active_tenant = Tenant.objects.filter(slug="jamuna-group").first() or Tenant.objects.first()

        validated_data["tenant_id"] = active_tenant.id

        with tenant_context(active_tenant):
            role = super().create(validated_data)

            template_perms: dict[int, list[str]] = {}
            if template_code:
                tpl_role = Role.unscoped_objects.filter(
                    tenant_id=role.tenant_id, code=template_code, deleted_at__isnull=True
                ).first() or Role.unscoped_objects.filter(code=template_code, deleted_at__isnull=True).first()
                if tpl_role:
                    for p in RolePermission.unscoped_objects.filter(role=tpl_role, deleted_at__isnull=True):
                        template_perms[p.module_number] = list(p.actions or [])

            def _populate_role_perms(target_role: Role) -> None:
                for mod_num in range(1, 44):
                    if mod_num in template_perms:
                        actions = list(template_perms[mod_num])
                    elif code in ("super-admin", "admin"):
                        actions = ["view", "create", "edit", "delete"]
                    elif mod_num in (1, 10, 32, 34, 35, 36):
                        actions = ["view", "create"]
                    else:
                        actions = []
                    RolePermission.unscoped_objects.update_or_create(
                        tenant_id=target_role.tenant_id,
                        role=target_role,
                        module_number=mod_num,
                        defaults={"actions": actions},
                    )

            _populate_role_perms(role)

        # Also replicate custom role across other demo tenants so role tabs stay consistent
        for other_tenant in Tenant.objects.exclude(id=role.tenant_id):
            with tenant_context(other_tenant):
                other_role, created_other = Role.unscoped_objects.get_or_create(
                    tenant=other_tenant,
                    code=role.code,
                    defaults={
                        "name": role.name,
                        "badge_label": role.badge_label,
                        "description": role.description,
                        "display_order": role.display_order,
                        "is_system_role": role.is_system_role,
                        "can_view_confidential_salary": role.can_view_confidential_salary,
                        "can_view_confidential_medical": role.can_view_confidential_medical,
                        "has_approval_authority": role.has_approval_authority,
                    },
                )
                if created_other:
                    _populate_role_perms(other_role)

        return role


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
