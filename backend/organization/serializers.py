"""Serializers for Company, Branch, Department, Designation, and Employee with field-level masking."""
from typing import Any

from rest_framework import serializers

from .models import (
    Branch,
    Company,
    CostCenter,
    Department,
    Designation,
    EmergencyContact,
    Employee,
    EmployeeDocument,
    EmployeeExperience,
    EmployeeQualification,
    EmploymentRecord,
    FamilyMember,
    Grade,
    ReportingLine,
    Section,
)


class CompanySerializer(serializers.ModelSerializer):
    branch_count = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "name_bn",
            "code",
            "registration_no",
            "tin_number",
            "address",
            "currency",
            "timezone",
            "is_primary",
            "branch_count",
            "employee_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_branch_count(self, obj: Company) -> int:
        return obj.organization_branch_set.filter(deleted_at__isnull=True).count()

    def get_employee_count(self, obj: Company) -> int:
        return obj.organization_employee_set.filter(deleted_at__isnull=True).count()


class BranchSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Branch
        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "name_bn",
            "code",
            "city",
            "address",
            "latitude",
            "longitude",
            "geofence_radius_meters",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DepartmentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    actual_headcount = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            "id",
            "company",
            "company_name",
            "branch",
            "branch_name",
            "name",
            "name_bn",
            "code",
            "approved_headcount",
            "actual_headcount",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_actual_headcount(self, obj: Department) -> int:
        return obj.employees.filter(deleted_at__isnull=True).count()


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = [
            "id",
            "company",
            "name",
            "code",
            "rank_order",
            "min_gross_bdt",
            "max_gross_bdt",
            "currency",
        ]
        read_only_fields = ["id"]


class DesignationSerializer(serializers.ModelSerializer):
    grade_name = serializers.CharField(source="grade.name", read_only=True)

    class Meta:
        model = Designation
        fields = [
            "id",
            "company",
            "title",
            "title_bn",
            "code",
            "grade",
            "grade_name",
        ]
        read_only_fields = ["id"]


class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = ["id", "company", "name", "code", "budget_bdt", "currency"]
        read_only_fields = ["id"]


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "company", "department", "name", "code"]
        read_only_fields = ["id"]


class EmployeeSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    designation_title = serializers.CharField(source="designation.title", read_only=True)
    manager_name = serializers.CharField(source="manager.full_name", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    role_code = serializers.CharField(source="role.code", read_only=True)
    role_badge = serializers.CharField(source="role.badge_label", read_only=True)
    national_id_masked = serializers.SerializerMethodField()
    bank_account_masked = serializers.SerializerMethodField()
    gross_salary_display = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "id",
            "company",
            "company_name",
            "employee_code",
            "full_name",
            "full_name_bn",
            "work_email",
            "phone",
            "joining_date",
            "employment_status",
            "branch",
            "branch_name",
            "department",
            "department_name",
            "designation",
            "designation_title",
            "grade",
            "cost_center",
            "manager",
            "manager_name",
            "role",
            "role_name",
            "role_code",
            "role_badge",
            "gross_salary_bdt",
            "bank_name",
            "national_id_masked",
            "bank_account_masked",
            "gross_salary_display",
            "currency",
            "blood_group",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "gross_salary_bdt": {"write_only": True, "required": False},
        }

    def _sync_user_and_role(self, employee: Employee) -> None:
        from accounts.models import DataScope, Role, User

        role = employee.role
        if not role and employee.tenant_id:
            role = Role.unscoped_objects.filter(
                tenant_id=employee.tenant_id, code="user", deleted_at__isnull=True
            ).first()
            if role:
                employee.role = role
                Employee.unscoped_objects.filter(pk=employee.pk).update(role=role)

        if not role or not employee.work_email:
            return

        is_super = role.code == "super-admin"
        is_admin = role.code in ("super-admin", "admin", "hr-director")
        is_mgr = role.code in ("manager", "asst-manager", "line-manager")
        exp_mode = (
            User.ExperienceMode.ADMIN
            if is_admin
            else (User.ExperienceMode.MANAGER if is_mgr else User.ExperienceMode.EMPLOYEE)
        )

        user = employee.user or User.objects.filter(email=employee.work_email).first()
        if not user:
            user = User.objects.create_user(
                email=employee.work_email,
                password="Pass1234!",
                full_name=employee.full_name,
                full_name_bn=employee.full_name_bn,
                phone=employee.phone,
                tenant=employee.tenant,
                default_company=employee.company,
                experience_mode=exp_mode,
                is_platform_admin=is_super,
                can_view_salary=bool(is_admin or role.can_view_confidential_salary),
                can_view_medical=bool(is_admin or role.can_view_confidential_medical),
                has_approval_authority=bool(is_admin or is_mgr or role.has_approval_authority),
            )
            user.allowed_companies.add(employee.company)
        else:
            user.full_name = employee.full_name
            user.full_name_bn = employee.full_name_bn
            user.experience_mode = exp_mode
            user.is_platform_admin = is_super
            user.can_view_salary = bool(is_admin or role.can_view_confidential_salary)
            user.can_view_medical = bool(is_admin or role.can_view_confidential_medical)
            user.has_approval_authority = bool(is_admin or is_mgr or role.has_approval_authority)
            user.save()

        if employee.user_id != user.id:
            employee.user = user
            Employee.unscoped_objects.filter(pk=employee.pk).update(user=user)

        DataScope.unscoped_objects.filter(user=user).exclude(role=role).delete()
        DataScope.unscoped_objects.update_or_create(
            tenant=employee.tenant,
            user=user,
            role=role,
            defaults={
                "scope_type": DataScope.ScopeType.ALL_TENANT,
                "company_ids": [str(employee.company_id)],
            },
        )

    def create(self, validated_data: dict[str, Any]) -> Employee:
        employee = super().create(validated_data)
        self._sync_user_and_role(employee)
        return employee

    def update(self, instance: Employee, validated_data: dict[str, Any]) -> Employee:
        employee = super().update(instance, validated_data)
        self._sync_user_and_role(employee)
        return employee

    def get_national_id_masked(self, obj: Employee) -> str:
        return obj.get_masked_field("national_id_encrypted", visible_tail=4)

    def get_bank_account_masked(self, obj: Employee) -> str:
        return obj.get_masked_field("bank_account_encrypted", visible_tail=4)

    def get_gross_salary_display(self, obj: Employee) -> Any:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and (getattr(user, "can_view_salary", False) or getattr(user, "is_platform_admin", False)):
            return str(obj.gross_salary_bdt)
        return "•••••••• (Restricted)"


class EmergencyContactSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = EmergencyContact
        fields = ["id", "employee", "employee_name", "name", "relationship", "phone", "address", "is_primary"]
        read_only_fields = ["id"]


class FamilyMemberSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = FamilyMember
        fields = [
            "id",
            "employee",
            "employee_name",
            "full_name",
            "relationship",
            "date_of_birth",
            "is_nominee",
            "nominee_share_pct",
        ]
        read_only_fields = ["id"]


class EmployeeQualificationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = EmployeeQualification
        fields = [
            "id",
            "employee",
            "employee_name",
            "degree_or_certification",
            "institution",
            "passing_year",
            "result_or_cgpa",
        ]
        read_only_fields = ["id"]


class EmployeeExperienceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = EmployeeExperience
        fields = [
            "id",
            "employee",
            "employee_name",
            "employer_name",
            "designation_held",
            "start_date",
            "end_date",
            "responsibilities",
        ]
        read_only_fields = ["id"]


class EmploymentRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    designation_title = serializers.CharField(source="designation.title", read_only=True)

    class Meta:
        model = EmploymentRecord
        fields = [
            "id",
            "company",
            "company_name",
            "employee",
            "employee_name",
            "contract_reference",
            "contract_type",
            "department",
            "department_name",
            "designation",
            "designation_title",
            "branch",
            "effective_from",
            "effective_to",
            "change_reason",
            "status",
        ]
        read_only_fields = ["id"]


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = EmployeeDocument
        fields = [
            "id",
            "employee",
            "employee_name",
            "document_type",
            "title",
            "issue_date",
            "expiry_date",
            "storage_key",
            "is_verified",
        ]
        read_only_fields = ["id"]


class ReportingLineSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    manager_name = serializers.CharField(source="manager.full_name", read_only=True)

    class Meta:
        model = ReportingLine
        fields = [
            "id",
            "employee",
            "employee_name",
            "manager",
            "manager_name",
            "effective_from",
            "effective_to",
            "change_reason",
        ]
        read_only_fields = ["id"]

