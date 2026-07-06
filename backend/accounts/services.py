from accounts.models import Menu, Permission, Role, UserAccessProfile, UserRole


DEFAULT_SYSTEM_MENUS = [
    {"name": "客户中心", "code": "customers", "path": "/customers", "order_index": 10},
    {"name": "项目中心", "code": "devices", "path": "/devices", "order_index": 20},
    {"name": "设备中心", "code": "device-center", "path": "/device-center", "order_index": 30},
    {"name": "销售中心", "code": "sales", "path": "/sales", "order_index": 40},
    {"name": "合同中心", "code": "contracts", "path": "/contracts", "order_index": 50},
    {"name": "产品型号", "code": "products", "path": "/products", "order_index": 60},
    {"name": "人员管理", "code": "people", "path": "/people", "order_index": 70},
    {"name": "系统管理", "code": "system", "path": "/system", "order_index": 80},
]


def ensure_default_menus():
    existing_codes = set(Menu.objects.values_list("code", flat=True))
    missing_items = [item for item in DEFAULT_SYSTEM_MENUS if item["code"] not in existing_codes]
    if missing_items:
        Menu.objects.bulk_create([Menu(**item) for item in missing_items])
    return Menu.objects.all()


def get_user_role_ids(user):
    return list(UserRole.objects.filter(user=user).values_list("role_id", flat=True))


def get_user_bound_person(user):
    return getattr(user, "person_profile", None)


def get_user_sales_scope(user):
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        return None

    profile = getattr(user, "access_profile", None)
    if not profile:
        return None

    if profile.data_scope_type == UserAccessProfile.DATA_SCOPE_ALL:
        return None
    if profile.data_scope_type == UserAccessProfile.DATA_SCOPE_SELF:
        person = get_user_bound_person(user)
        if person and person.person_type == "sales":
            return {person.id}
        return set()

    return set(profile.sales_scopes.values_list("sales_person_id", flat=True))


def get_user_menus(user):
    ensure_default_menus()
    if user.is_superuser:
        return Menu.objects.filter(status="active").order_by("order_index", "id")
    role_ids = get_user_role_ids(user)
    menu_ids = Permission.objects.filter(role_id__in=role_ids).values_list("menu_id", flat=True).distinct()
    return Menu.objects.filter(id__in=menu_ids, status="active").order_by("order_index", "id")


def get_user_permissions(user):
    if user.is_superuser:
        return [["*", "*"]]
    role_ids = get_user_role_ids(user)
    return [list(item) for item in Permission.objects.filter(role_id__in=role_ids).values_list("menu__code", "action")]


def has_menu_action(user, menu_code, action):
    if user.is_superuser:
        return True
    role_ids = get_user_role_ids(user)
    return Permission.objects.filter(role_id__in=role_ids, menu__code=menu_code, action=action).exists()


def filter_queryset_by_sales_scope(queryset, user, sales_field="sales_person_id"):
    sales_ids = get_user_sales_scope(user)
    if sales_ids is None:
        return queryset
    if not sales_ids:
        return queryset.none()
    return queryset.filter(**{f"{sales_field}__in": list(sales_ids)})


