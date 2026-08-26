from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import Menu, Permission, Role, TokenActivity, UserRole
from accounts.serializers import MenuSerializer, PermissionSerializer, RoleSerializer, UserRoleSerializer, UserSerializer
from accounts.services import ensure_default_menus, get_user_menus, get_user_permissions, get_user_role_ids
from accounts.permissions import MenuActionPermission


class SystemModelViewSet(viewsets.ModelViewSet):
    permission_classes = [MenuActionPermission]
    menu_code = "system"


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "用户名或密码错误"}, status=status.HTTP_400_BAD_REQUEST)
    token, _ = Token.objects.get_or_create(user=user)
    TokenActivity.objects.update_or_create(token=token, defaults={"last_active_at": timezone.now()})
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["GET"])
def current_user_view(request):
    menus = get_user_menus(request.user)
    data = UserSerializer(request.user).data
    data["role_ids"] = get_user_role_ids(request.user)
    data["menus"] = MenuSerializer(menus, many=True).data
    data["permissions"] = get_user_permissions(request.user)
    return Response(data)


class UserViewSet(SystemModelViewSet):
    queryset = User.objects.prefetch_related(
        "user_roles__role",
        "access_profile__sales_scopes__sales_person",
    ).all().order_by("id")
    serializer_class = UserSerializer

    def get_queryset(self):
        return super().get_queryset().exclude(username=settings.LICENSE_OPERATOR_USERNAME)


class RoleViewSet(SystemModelViewSet):
    queryset = Role.objects.all().order_by("id")
    serializer_class = RoleSerializer


class MenuViewSet(SystemModelViewSet):
    queryset = Menu.objects.all().order_by("order_index", "id")
    serializer_class = MenuSerializer

    def get_queryset(self):
        ensure_default_menus()
        return super().get_queryset()


class PermissionViewSet(SystemModelViewSet):
    queryset = Permission.objects.select_related("role", "menu").all().order_by("id")
    serializer_class = PermissionSerializer


class UserRoleViewSet(SystemModelViewSet):
    queryset = UserRole.objects.select_related("user", "role").all().order_by("id")
    serializer_class = UserRoleSerializer
