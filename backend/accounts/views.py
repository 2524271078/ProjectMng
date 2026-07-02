from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from accounts.models import Menu, Permission, Role, UserRole
from accounts.serializers import MenuSerializer, PermissionSerializer, RoleSerializer, UserRoleSerializer, UserSerializer


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
    role_ids = UserRole.objects.filter(user=request.user).values_list("role_id", flat=True)
    menu_ids = Permission.objects.filter(role_id__in=role_ids).values_list("menu_id", flat=True).distinct()
    menus = Menu.objects.filter(id__in=menu_ids, status="active").order_by("order_index", "id")
    data = UserSerializer(request.user).data
    data["menus"] = MenuSerializer(menus, many=True).data
    data["permissions"] = list(Permission.objects.filter(role_id__in=role_ids).values_list("menu__code", "action"))
    return Response(data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
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
