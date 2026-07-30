from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.services import get_user_role_ids, has_menu_action


SUPPORTED_MENU_ACTIONS = {
    "customers": {"view", "create", "edit", "delete"},
    "devices": {"view", "create", "edit", "delete"},
    "device-center": {"view"},
    "sales": {"view"},
    "contracts": {"view", "create"},
    "products": {"view", "create", "edit", "delete"},
    "people": {"view", "create", "edit", "delete"},
    "system": {"view", "create", "edit", "delete"},
}


class MenuActionPermission(BasePermission):
    """Authorize mutations against the CRUD action granted for the owning menu."""

    message = "当前角色没有执行此操作的权限。"

    def has_permission(self, request, view):
        # Route guards enforce view access in the UI.  Keep supporting legacy
        # API-only users with no role assignments while enforcing every write
        # for users managed through role permissions.
        if request.method in SAFE_METHODS or not get_user_role_ids(request.user):
            return True
        menu_code = getattr(view, "menu_code", "")
        if not menu_code:
            return True
        action = {
            "POST": "create",
            "PUT": "edit",
            "PATCH": "edit",
            "DELETE": "delete",
        }.get(request.method)
        action = getattr(view, "permission_action_overrides", {}).get(getattr(view, "action", ""), action)
        menu_codes = menu_code if isinstance(menu_code, (list, tuple, set)) else [menu_code]
        return bool(action and any(
            action in SUPPORTED_MENU_ACTIONS.get(code, {"view"}) and has_menu_action(request.user, code, action)
            for code in menu_codes
        ))
