from django.conf import settings
from django.db import models


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
    role = models.ForeignKey(Role, related_name="permissions", on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, related_name="permissions", on_delete=models.CASCADE)
    action = models.CharField(max_length=64, default="view")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["role", "menu", "action"], name="uniq_role_menu_action")]


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user_roles", on_delete=models.CASCADE)
    role = models.ForeignKey(Role, related_name="user_roles", on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role")]
