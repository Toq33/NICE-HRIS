"""Serializers for Platform Admin (Plans, Tenants, EnabledModules, Module Registry)."""
from rest_framework import serializers

from organization.models import Company, Employee

from .models import EnabledModule, Plan, Tenant
from .services import provision_tenant


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id",
            "code",
            "name",
            "description",
            "max_employees",
            "max_companies",
            "monthly_price_bdt",
            "currency",
            "default_module_numbers",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EnabledModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnabledModule
        fields = [
            "id",
            "module_number",
            "module_slug",
            "module_name",
            "module_group",
            "phase",
            "is_enabled",
            "updated_at",
        ]
        read_only_fields = ["id", "module_slug", "module_name", "module_group", "phase", "updated_at"]


class TenantSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    company_count = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    enabled_module_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "name_bn",
            "slug",
            "status",
            "plan",
            "plan_name",
            "multi_company_enabled",
            "employee_limit",
            "primary_domain",
            "default_currency",
            "default_timezone",
            "lakh_grouping_enabled",
            "weekly_off_days",
            "company_count",
            "employee_count",
            "enabled_module_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_company_count(self, obj: Tenant) -> int:
        return Company.unscoped_objects.filter(tenant=obj, deleted_at__isnull=True).count()

    def get_employee_count(self, obj: Tenant) -> int:
        return Employee.unscoped_objects.filter(tenant=obj, deleted_at__isnull=True).count()

    def get_enabled_module_count(self, obj: Tenant) -> int:
        return obj.enabled_modules.filter(is_enabled=True).count()

    def create(self, validated_data: dict) -> Tenant:
        return provision_tenant(
            name=validated_data["name"],
            name_bn=validated_data.get("name_bn", ""),
            slug=validated_data["slug"],
            plan=validated_data["plan"],
            multi_company_enabled=validated_data.get("multi_company_enabled", False),
            employee_limit=validated_data.get("employee_limit"),
            status=validated_data.get("status", Tenant.Status.ACTIVE),
        )
