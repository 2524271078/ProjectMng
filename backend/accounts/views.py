from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import Menu, Permission, Role, UserRole
from accounts.serializers import MenuSerializer, PermissionSerializer, RoleSerializer, UserRoleSerializer, UserSerializer
from accounts.services import get_user_menus, get_user_permissions, get_user_role_ids


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "用户名或密码错误"}, status=status.HTTP_400_BAD_REQUEST)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["GET"])
def current_user_view(request):
    menus = get_user_menus(request.user)
    data = UserSerializer(request.user).data
    data["role_ids"] = get_user_role_ids(request.user)
    data["menus"] = MenuSerializer(menus, many=True).data
    data["permissions"] = get_user_permissions(request.user)
    return Response(data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related(
        "user_roles__role",
        "access_profile__sales_scopes__sales_person",
    ).all().order_by("id")
    serializer_class = UserSerializer


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by("id")
    serializer_class = RoleSerializer


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all().order_by("order_index", "id")
    serializer_class = MenuSerializer


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.select_related("role", "menu").all().order_by("id")
    serializer_class = PermissionSerializer


class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.select_related("user", "role").all().order_by("id")
    serializer_class = UserRoleSerializer
