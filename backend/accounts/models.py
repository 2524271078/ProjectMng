from django.conf import settings
from django.db import models
from rest_framework.authtoken.models import Token


class Role(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True)
    remark = models.TextField(blank=True, default="")
    status = models.CharField(max_length=32, default="active", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Menu(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True)
    path = models.CharField(max_length=200, blank=True, default="")
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.CASCADE)
    icon = models.CharField(max_length=100, blank=True, default="")
    order_index = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=32, default="active", db_index=True)

    class Meta:
        ordering = ["order_index", "id"]

    def __str__(self):
        return self.name


class Permission(models.Model):
    ACTION_VIEW = "view"
    ACTION_CREATE = "create"
    ACTION_EDIT = "edit"
    ACTION_DELETE = "delete"
    ACTION_CHOICES = [
        (ACTION_VIEW, "查看"),
        (ACTION_CREATE, "新增"),
        (ACTION_EDIT, "编辑"),
        (ACTION_DELETE, "删除"),
    ]

    role = models.ForeignKey(Role, related_name="permissions", on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, related_name="permissions", on_delete=models.CASCADE)
    action = models.CharField(max_length=64, default=ACTION_VIEW, choices=ACTION_CHOICES)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["role", "menu", "action"], name="uniq_role_menu_action")]


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user_roles", on_delete=models.CASCADE)
    role = models.ForeignKey(Role, related_name="user_roles", on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role")]


class UserAccessProfile(models.Model):
    DATA_SCOPE_ALL = "all"
    DATA_SCOPE_SELF = "self"
    DATA_SCOPE_CUSTOM = "custom"
    DATA_SCOPE_CHOICES = [
        (DATA_SCOPE_ALL, "全部数据"),
        (DATA_SCOPE_SELF, "本人销售数据"),
        (DATA_SCOPE_CUSTOM, "自定义销售范围"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="access_profile", on_delete=models.CASCADE)
    data_scope_type = models.CharField(max_length=16, choices=DATA_SCOPE_CHOICES, default=DATA_SCOPE_CUSTOM)
    remark = models.TextField(blank=True, default="")
    status = models.CharField(max_length=32, default="active", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserSalesScope(models.Model):
    profile = models.ForeignKey(UserAccessProfile, related_name="sales_scopes", on_delete=models.CASCADE)
    sales_person = models.ForeignKey("projects.Person", related_name="user_sales_scopes", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "sales_person"], name="uniq_profile_sales_scope")]


class TokenActivity(models.Model):
    """Tracks API activity so Token authentication can expire idle sessions."""

    token = models.OneToOneField(Token, related_name="activity", on_delete=models.CASCADE)
    last_active_at = models.DateTimeField()
