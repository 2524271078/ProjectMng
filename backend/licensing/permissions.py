from django.conf import settings
from rest_framework.permissions import BasePermission


class IsLicenseOperator(BasePermission):
    message = "当前账号无权管理系统授权。"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.username == settings.LICENSE_OPERATOR_USERNAME
        )
