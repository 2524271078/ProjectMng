from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter

from accounts.views import MenuViewSet, PermissionViewSet, RoleViewSet, UserRoleViewSet, UserViewSet, current_user_view, login_view
from licensing.views import activate_license_view, license_request_view, license_status_view
from projects.views import AttachmentViewSet, attachment_upload, AuditLogViewSet, confirm_dashboard_reminder, ContractDeviceViewSet, ContractPartyViewSet, ContractViewSet, dashboard_overview, dashboard_reminders, DeviceModelViewSet, DeviceOperationRecordViewSet, DeviceServicePlanViewSet, DeviceServiceScheduleViewSet, DeviceViewSet, InspectionTaskViewSet, OrganizationViewSet, PersonViewSet, ProductLineViewSet, ProductVersionViewSet, ProductViewSet, ProjectContractViewSet, ProjectDeviceViewSet, ProjectViewSet, SalesCustomerRelationViewSet, ServiceStandardTemplateViewSet, contract_overview, customer_overview, device_overview, project_overview, sales_customer_relations, sales_customers

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("roles", RoleViewSet)
router.register("menus", MenuViewSet)
router.register("permissions", PermissionViewSet)
router.register("user-roles", UserRoleViewSet)
router.register("organizations", OrganizationViewSet)
router.register("people", PersonViewSet)
router.register("sales-customer-relations", SalesCustomerRelationViewSet)
router.register("product-lines", ProductLineViewSet)
router.register("products", ProductViewSet)
router.register("product-versions", ProductVersionViewSet)
router.register("device-models", DeviceModelViewSet)
router.register("devices", DeviceViewSet)
router.register("projects", ProjectViewSet)
router.register("project-devices", ProjectDeviceViewSet)
router.register("service-standard-templates", ServiceStandardTemplateViewSet)
router.register("device-service-plans", DeviceServicePlanViewSet)
router.register("device-service-schedules", DeviceServiceScheduleViewSet)
router.register("inspection-tasks", InspectionTaskViewSet)
router.register("device-operation-records", DeviceOperationRecordViewSet)
router.register("project-contracts", ProjectContractViewSet)
router.register("contracts", ContractViewSet)
router.register("contract-devices", ContractDeviceViewSet)
router.register("contract-parties", ContractPartyViewSet)
router.register("attachments", AttachmentViewSet)
router.register("audit-logs", AuditLogViewSet)


def root_view(request):
    return JsonResponse({
        "service": "项目设备管理系统 API",
        "api_base": "/api/",
        "admin": "/admin/",
        "frontend_dev": "http://127.0.0.1:5173/",
    })

urlpatterns = [
    path("", root_view),
    path("admin/", admin.site.urls),
    path("api/auth/login/", login_view),
    path("api/auth/me/", current_user_view),
    path("api/license/", license_status_view),
    path("api/license/request/", license_request_view),
    path("api/license/activate/", activate_license_view),
    path("api/dashboard-overview/", dashboard_overview),
    path("api/dashboard-reminders/", dashboard_reminders),
    path("api/dashboard-reminders/confirm/", confirm_dashboard_reminder),
    path("api/sales/<int:pk>/customers/", sales_customers),
    path("api/sales/<int:pk>/customer-relations/", sales_customer_relations),
    path("api/customers/<int:pk>/overview/", customer_overview),
    path("api/devices/<int:pk>/overview/", device_overview),
    path("api/projects/<int:pk>/overview/", project_overview),
    path("api/contracts/<int:pk>/overview/", contract_overview),
    path("api/attachments/upload/", attachment_upload),
    path("api/", include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
