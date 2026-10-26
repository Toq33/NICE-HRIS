"""Identity, Users, Roles, Permissions, DataScope, and LoginHistory (Module 39)."""
from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from core.models import SensitiveFieldMixin, TenantModel
from core.uuid7 import uuid7


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> "User":
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_platform_admin", True)
        extra_fields.setdefault("experience_mode", "ADMIN")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, SensitiveFieldMixin):
    """Multi-tenant User account supporting Admin/HR, Manager, and Employee experiences."""

    class ExperienceMode(models.TextChoices):
        ADMIN = "ADMIN", "HR / Admin"
        MANAGER = "MANAGER", "Manager (Module 33)"
        EMPLOYEE = "EMPLOYEE", "Employee (Module 32)"

    SENSITIVE_ENCRYPTED_FIELDS = ("totp_secret",)

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=160)
    full_name_bn = models.CharField(max_length=160, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")

    tenant = models.ForeignKey(
        "platform_admin.Tenant",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        db_index=True,
    )
    default_company = models.ForeignKey(
        "organization.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_users",
    )
    allowed_companies = models.ManyToManyField(
        "organization.Company",
        blank=True,
        related_name="permitted_users",
    )

    experience_mode = models.CharField(
        max_length=20,
        choices=ExperienceMode.choices,
        default=ExperienceMode.ADMIN,
    )
    is_platform_admin = models.BooleanField(default=False, db_index=True)
    can_view_salary = models.BooleanField(default=False)
    can_view_medical = models.BooleanField(default=False)
    has_approval_authority = models.BooleanField(default=False)

    totp_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=255, blank=True, default="")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["tenant", "email"]),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.encrypt_sensitive_fields()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"


class Role(TenantModel):
    """Tenant-defined role with separate view/edit vs approval authority and salary confidentiality."""

    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=60)
    description = models.TextField(blank=True, default="")
    is_system_role = models.BooleanField(default=False)
    can_view_confidential_salary = models.BooleanField(default=False)
    can_view_confidential_medical = models.BooleanField(default=False)
    has_approval_authority = models.BooleanField(default=False)

    class Meta:
        unique_together = [("tenant", "code")]
        indexes = [models.Index(fields=["tenant", "code"])]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class RolePermission(TenantModel):
    """Module + Action permission matrix entry (view, create, edit, delete, approve, export)."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    module_number = models.PositiveSmallIntegerField(db_index=True)
    actions = models.JSONField(default=list)

    class Meta:
        unique_together = [("tenant", "role", "module_number")]
        indexes = [models.Index(fields=["tenant", "role", "module_number"])]


class DataScope(TenantModel):
    """Assigns a Role to a User with a specific organizational data scope."""

    class ScopeType(models.TextChoices):
        ALL_TENANT = "ALL_TENANT", "Entire Tenant"
        COMPANIES = "COMPANIES", "Specific Companies"
        BRANCHES = "BRANCHES", "Specific Branches"
        DEPARTMENTS = "DEPARTMENTS", "Specific Departments"
        OWN_AND_DIRECT_REPORTS = "OWN_AND_DIRECT_REPORTS", "Own & Direct Reports"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="data_scopes")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_scopes")
    scope_type = models.CharField(
        max_length=32,
        choices=ScopeType.choices,
        default=ScopeType.ALL_TENANT,
    )
    company_ids = models.JSONField(default=list, blank=True)
    branch_ids = models.JSONField(default=list, blank=True)
    department_ids = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = [("tenant", "user", "role")]
        indexes = [models.Index(fields=["tenant", "user"])]


class LoginHistory(models.Model):
    """Immutable login audit trail (Module 40 foundation)."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="login_events")
    email_attempted = models.EmailField()
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")
    succeeded = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant_id", "created_at"])]
