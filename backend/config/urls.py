from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views import MenuViewSet, PermissionViewSet, RoleViewSet, UserRoleViewSet, UserViewSet, current_user_view, login_view
from projects.views import AttachmentViewSet, AuditLogViewSet, ContractDeviceViewSet, ContractPartyViewSet, ContractViewSet, DeviceModelViewSet, DeviceViewSet, OrganizationViewSet, PersonViewSet, ProductViewSet, SalesCustomerRelationViewSet, contract_overview, customer_overview, device_overview, sales_customers

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("roles", RoleViewSet)
router.register("menus", MenuViewSet)
router.register("permissions", PermissionViewSet)
router.register("user-roles", UserRoleViewSet)
router.register("organizations", OrganizationViewSet)
router.register("people", PersonViewSet)
router.register("sales-customer-relations", SalesCustomerRelationViewSet)
router.register("products", ProductViewSet)
router.register("device-models", DeviceModelViewSet)
router.register("devices", DeviceViewSet)
router.register("contracts", ContractViewSet)
router.register("contract-devices", ContractDeviceViewSet)
router.register("contract-parties", ContractPartyViewSet)
router.register("attachments", AttachmentViewSet)
router.register("audit-logs", AuditLogViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", login_view),
    path("api/auth/me/", current_user_view),
    path("api/sales/<int:pk>/customers/", sales_customers),
    path("api/customers/<int:pk>/overview/", customer_overview),
    path("api/devices/<int:pk>/overview/", device_overview),
    path("api/contracts/<int:pk>/overview/", contract_overview),
    path("api/", include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
