from math import ceil

from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import action, api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, viewsets

from accounts.services import filter_queryset_by_sales_scope, get_user_sales_scope
from projects.models import Attachment, AuditLog, Contract, ContractDevice, ContractParty, Device, DeviceModel, DeviceOperationRecord, DeviceServicePlan, InspectionTask, Organization, Person, Product, ProductLine, ProductVersion, Project, ProjectContract, ProjectDevice, SalesCustomerRelation, ServiceStandardTemplate
from projects.serializers import AttachmentSerializer, AuditLogSerializer, ContractDeviceSerializer, ContractPartySerializer, ContractSerializer, DeviceModelSerializer, DeviceOperationRecordSerializer, DeviceSerializer, DeviceServicePlanSerializer, InspectionTaskSerializer, OrganizationSerializer, PersonSerializer, ProductSerializer, ProductLineSerializer, ProductVersionSerializer, ProjectSerializer, ProjectContractSerializer, ProjectDeviceSerializer, SalesCustomerRelationSerializer, ServiceStandardTemplateSerializer


class SoftDeleteModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        model = queryset.model
        if any(field.name == "is_deleted" for field in model._meta.fields):
            queryset = queryset.filter(is_deleted=False)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page_items, meta = paginate_queryset(request, queryset)
        serializer = self.get_serializer(page_items, many=True)
        return Response({**meta, "results": serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            if hasattr(instance, "updated_by") and request.user.is_authenticated:
                instance.updated_by = request.user
            instance.save(update_fields=["is_deleted", "updated_at", "updated_by"] if hasattr(instance, "updated_by") else ["is_deleted"])
            return Response(status=status.HTTP_204_NO_CONTENT)
        return super().destroy(request, *args, **kwargs)


def apply_search(queryset, search_value, search_fields):
    if not search_value:
        return queryset

    conditions = Q()
    for field in search_fields:
        conditions |= Q(**{f"{field}__icontains": search_value})
    return queryset.filter(conditions)


def parse_query_int(raw_value):
    value = (raw_value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def ensure_pagination_ordering(queryset):
    pk_name = queryset.model._meta.pk.name

    if queryset.query.order_by:
        ordering = list(queryset.query.order_by)
    elif queryset.query.default_ordering and queryset.model._meta.ordering:
        ordering = list(queryset.model._meta.ordering)
    else:
        ordering = []

    normalized = [field.lstrip("-") for field in ordering if isinstance(field, str)]
    if pk_name not in normalized:
        ordering.append(pk_name)

    return queryset.order_by(*ordering) if ordering else queryset.order_by(pk_name)


def build_paginated_response(request, queryset, build_results):
    page_items, meta = paginate_queryset(request, queryset)
    return Response({**meta, "results": build_results(page_items)})


def paginate_queryset(request, queryset, default_page_size=10):
    page = parse_query_int(request.query_params.get("page"))
    page_size = parse_query_int(request.query_params.get("page_size"))

    if page is None or page <= 0:
        page = 1
    if page_size is None or page_size <= 0:
        page_size = default_page_size
    else:
        page_size = min(page_size, 100)

    queryset = ensure_pagination_ordering(queryset)

    count = queryset.count()
    total_pages = max(ceil(count / page_size), 1) if count else 1
    start = (page - 1) * page_size
    end = start + page_size

    return queryset[start:end], {
        "count": count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def resolve_device_model_scope(query_params):
    # Device model scope uses the most specific valid node only; it is not a combined constraint.
    scope_candidates = [
        ("product_version_id", parse_query_int(query_params.get("product_version"))),
        ("product_id", parse_query_int(query_params.get("product"))),
        ("product__product_line_id", parse_query_int(query_params.get("product_line"))),
    ]
    for lookup, value in scope_candidates:
        if value is not None:
            return lookup, value
    return None, None


def apply_device_model_scope(queryset, query_params):
    lookup, value = resolve_device_model_scope(query_params)
    if lookup is None:
        return queryset
    return queryset.filter(**{lookup: value})


def customer_ids_for_user(user):
    sales_ids = get_user_sales_scope(user)
    if sales_ids is None:
        return None
    if not sales_ids:
        return set()
    return set(
        SalesCustomerRelation.objects.filter(is_deleted=False, sales_person_id__in=sales_ids).values_list("customer_org_id", flat=True)
    )


def filter_customer_queryset_for_user(queryset, user):
    customer_ids = customer_ids_for_user(user)
    if customer_ids is None:
        return queryset
    if not customer_ids:
        return queryset.none()
    return queryset.filter(id__in=customer_ids)


def filter_device_queryset_for_user(queryset, user):
    sales_ids = get_user_sales_scope(user)
    if sales_ids is None:
        return queryset
    if not sales_ids:
        return queryset.none()
    return queryset.filter(
        Q(sales_person_id__in=sales_ids)
        | Q(sales_person__isnull=True, project_devices__is_deleted=False, project_devices__project__sales_person_id__in=sales_ids)
    ).distinct()


def filter_devices_by_current_signing_subject(queryset, signing_subject, customer=None):
    if signing_subject not in {Project.SIGNING_SUBJECT_DIRECT, Project.SIGNING_SUBJECT_AGENT}:
        return queryset

    latest_bindings = ProjectDevice.objects.filter(
        device_id=OuterRef("pk"),
        is_deleted=False,
        project__is_deleted=False,
    )
    if customer:
        latest_bindings = latest_bindings.filter(project__customer_org=customer)

    return queryset.annotate(
        current_project_signing_subject=Subquery(
            latest_bindings.order_by("-service_end_date", "-updated_at", "-id").values("project__signing_subject")[:1]
        )
    ).filter(current_project_signing_subject=signing_subject)


def generate_project_no():
    prefix = f"PRJ-{timezone.localdate():%Y%m%d}-"
    sequence_numbers = []
    for project_no in Project.all_objects.filter(project_no__startswith=prefix).values_list("project_no", flat=True):
        suffix = project_no.removeprefix(prefix)
        if suffix.isdigit():
            sequence_numbers.append(int(suffix))
    return f"{prefix}{max(sequence_numbers, default=0) + 1:04d}"


class OrganizationViewSet(SoftDeleteModelViewSet):
    queryset = Organization.objects.all().order_by("id")
    serializer_class = OrganizationSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = super().get_queryset()
        org_type = self.request.query_params.get("org_type", "").strip()
        search_value = self.request.query_params.get("search", "").strip()
        if org_type:
            queryset = queryset.filter(org_type=org_type)
        if org_type == "customer":
            queryset = filter_customer_queryset_for_user(queryset, self.request.user)
        return apply_search(queryset, search_value, ["name", "region", "org_type"])

    @action(detail=True, methods=["get"], url_path="devices")
    def devices(self, request, pk=None):
        customer_queryset = filter_customer_queryset_for_user(Organization.objects.filter(org_type="customer"), request.user)
        customer = get_object_or_404(customer_queryset, pk=pk)
        queryset = Device.objects.select_related("device_model", "device_model__product", "device_model__product_version", "customer_org", "sales_person", "ops_person").filter(
            Q(customer_org=customer) |
            Q(project_devices__project__customer_org=customer, project_devices__is_deleted=False),
            is_deleted=False,
        ).distinct()
        queryset = filter_device_queryset_for_user(queryset, request.user)
        queryset = apply_search(queryset, request.query_params.get("search", "").strip(), [
            "name",
            "serial_number",
            "device_model__model_name",
        ])
        queryset = filter_devices_by_current_signing_subject(queryset, request.query_params.get("signing_subject", ""), customer)
        return build_paginated_response(
            request,
            queryset,
            lambda page_items: [device_summary(item, latest_project_device_service(item, customer)) for item in page_items],
        )

    @action(detail=True, methods=["get"], url_path="projects")
    def projects(self, request, pk=None):
        customer = get_object_or_404(filter_customer_queryset_for_user(self.get_queryset(), request.user), pk=pk)
        queryset = customer.projects.filter(is_deleted=False).select_related("customer_contact", "sales_person")
        queryset = filter_queryset_by_sales_scope(queryset, request.user, "sales_person_id")
        return build_paginated_response(request, queryset, lambda page_items: [project_summary(item) for item in page_items])

    @action(detail=True, methods=["get"], url_path="contracts")
    def contracts(self, request, pk=None):
        customer = get_object_or_404(filter_customer_queryset_for_user(self.get_queryset(), request.user), pk=pk)
        queryset = customer.final_customer_contracts.filter(is_deleted=False).select_related("sales_person", "final_customer", "direct_buyer")
        queryset = filter_queryset_by_sales_scope(queryset, request.user, "sales_person_id")
        return build_paginated_response(request, queryset, lambda page_items: [contract_summary(item) for item in page_items])

    @action(detail=True, methods=["get"], url_path="contacts")
    def contacts(self, request, pk=None):
        customer = get_object_or_404(filter_customer_queryset_for_user(self.get_queryset(), request.user), pk=pk)
        queryset = customer.people.filter(person_type="customer_contact", is_deleted=False)
        return build_paginated_response(request, queryset, lambda page_items: [person_summary(item) for item in page_items])

    @action(detail=True, methods=["get"], url_path="sales")
    def sales(self, request, pk=None):
        customer = get_object_or_404(filter_customer_queryset_for_user(self.get_queryset(), request.user), pk=pk)
        queryset = customer.sales_relations.filter(is_deleted=False).select_related("sales_person")
        sales_ids = get_user_sales_scope(request.user)
        if sales_ids is not None:
            queryset = queryset.filter(sales_person_id__in=sales_ids) if sales_ids else queryset.none()
        return build_paginated_response(request, queryset, lambda page_items: [person_summary(item.sales_person) for item in page_items])


class PersonViewSet(SoftDeleteModelViewSet):
    queryset = Person.objects.select_related("organization", "user").all()
    serializer_class = PersonSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        person_type = self.request.query_params.get("person_type", "").strip()
        search_value = self.request.query_params.get("search", "").strip()
        if person_type:
            queryset = queryset.filter(person_type=person_type)
            if person_type == "sales":
                sales_ids = get_user_sales_scope(self.request.user)
                if sales_ids is not None:
                    queryset = queryset.filter(id__in=sales_ids) if sales_ids else queryset.none()
        return apply_search(queryset, search_value, ["name", "phone", "email"])


class SalesCustomerRelationViewSet(SoftDeleteModelViewSet):
    queryset = SalesCustomerRelation.objects.select_related("sales_person", "customer_org").all()
    serializer_class = SalesCustomerRelationSerializer


class ProductLineViewSet(SoftDeleteModelViewSet):
    queryset = ProductLine.objects.all().order_by("id")
    serializer_class = ProductLineSerializer


class ProductViewSet(SoftDeleteModelViewSet):
    queryset = Product.objects.select_related("product_line", "manufacturer").all().order_by("id")
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(product_line__isnull=False, product_line__is_deleted=False)


class ProductVersionViewSet(SoftDeleteModelViewSet):
    queryset = ProductVersion.objects.select_related("product").all().order_by("id")
    serializer_class = ProductVersionSerializer


class DeviceModelViewSet(SoftDeleteModelViewSet):
    queryset = DeviceModel.objects.select_related("product", "product_version", "manufacturer").all().order_by("id")
    serializer_class = DeviceModelSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = apply_device_model_scope(queryset, self.request.query_params)
        search_value = self.request.query_params.get("search", "").strip()
        return apply_search(queryset, search_value, ["model_name", "model_code", "product__name", "product_version__version_name"])


class DeviceViewSet(SoftDeleteModelViewSet):
    queryset = Device.objects.select_related("device_model", "customer_org", "sales_person", "ops_person").prefetch_related(
        "project_devices__project__customer_org",
        "project_devices__project__customer_contact",
        "project_devices__project__sales_person",
    ).all()
    serializer_class = DeviceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search_value = self.request.query_params.get("search", "").strip()
        queryset = apply_search(
            queryset,
            search_value,
            [
                "name",
                "serial_number",
                "device_model__model_name",
                "customer_org__name",
                "sales_person__name",
                "project_devices__project__customer_contact__name",
                "project_devices__project__sales_person__name",
            ],
        )
        queryset = queryset.filter(
            Q(customer_org__isnull=False, customer_org__is_deleted=False)
            | Q(project_devices__is_deleted=False, project_devices__project__is_deleted=False, project_devices__project__customer_org__is_deleted=False)
        )
        queryset = filter_device_queryset_for_user(queryset, self.request.user)
        queryset = filter_devices_by_current_signing_subject(queryset, self.request.query_params.get("signing_subject", ""))
        return queryset.distinct()


class ProjectViewSet(SoftDeleteModelViewSet):
    queryset = Project.objects.select_related("customer_org", "sales_person", "ops_person").all().order_by("id")
    serializer_class = ProjectSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search_value = self.request.query_params.get("search", "").strip()
        queryset = filter_queryset_by_sales_scope(queryset, self.request.user, "sales_person_id")
        return apply_search(queryset, search_value, ["name", "customer_org__name", "sales_person__name", "project_stage"])

    def perform_create(self, serializer):
        project_no = serializer.validated_data.get("project_no", "").strip()
        serializer.save(project_no=project_no or generate_project_no())

    @action(detail=True, methods=["get"], url_path="devices")
    def devices(self, request, pk=None):
        project = self.get_object()
        queryset = project.project_devices.filter(is_deleted=False).select_related("device", "device__device_model", "device__device_model__product", "device__device_model__product_version")
        return build_paginated_response(request, queryset, lambda page_items: [project_device_summary(item) for item in page_items])

    @action(detail=True, methods=["get"], url_path="contracts")
    def contracts(self, request, pk=None):
        project = self.get_object()
        queryset = project.project_contracts.filter(is_deleted=False).select_related("contract")
        return build_paginated_response(request, queryset, lambda page_items: [contract_summary(item.contract) for item in page_items])

    @action(detail=True, methods=["get"], url_path="attachments")
    def attachments(self, request, pk=None):
        project = self.get_object()
        queryset = Attachment.objects.filter(object_type="project", object_id=project.id)
        return build_paginated_response(
            request,
            queryset,
            lambda page_items: AttachmentSerializer(page_items, many=True, context={"request": request}).data,
        )


class ProjectDeviceViewSet(SoftDeleteModelViewSet):
    queryset = ProjectDevice.objects.select_related("project", "device", "device__device_model", "device__device_model__product", "device__device_model__product_version").all().order_by("id")
    serializer_class = ProjectDeviceSerializer


class ServiceStandardTemplateViewSet(SoftDeleteModelViewSet):
    queryset = ServiceStandardTemplate.objects.all().order_by("id")
    serializer_class = ServiceStandardTemplateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return apply_search(queryset, self.request.query_params.get("search", "").strip(), ["name", "code"])


class DeviceServicePlanViewSet(SoftDeleteModelViewSet):
    queryset = DeviceServicePlan.objects.select_related(
        "project_device__project",
        "project_device__device",
        "template",
        "ops_person",
    ).all().order_by("id")
    serializer_class = DeviceServicePlanSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_queryset_by_sales_scope(queryset, self.request.user, "project_device__project__sales_person_id")
        project_device_id = parse_query_int(self.request.query_params.get("project_device"))
        if project_device_id is not None:
            queryset = queryset.filter(project_device_id=project_device_id)
        device_id = parse_query_int(self.request.query_params.get("device"))
        if device_id is not None:
            queryset = queryset.filter(project_device__device_id=device_id)
        return queryset


class InspectionTaskViewSet(SoftDeleteModelViewSet):
    queryset = InspectionTask.objects.select_related(
        "service_plan__project_device__project",
        "service_plan__project_device__device",
        "assignee",
    ).all().order_by("planned_date", "id")
    serializer_class = InspectionTaskSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_queryset_by_sales_scope(queryset, self.request.user, "service_plan__project_device__project__sales_person_id")
        device_id = parse_query_int(self.request.query_params.get("device"))
        if device_id is not None:
            queryset = queryset.filter(service_plan__project_device__device_id=device_id)
        status_value = self.request.query_params.get("status", "").strip()
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset


class DeviceOperationRecordViewSet(SoftDeleteModelViewSet):
    queryset = DeviceOperationRecord.objects.select_related(
        "device",
        "project_device__project",
        "service_plan",
        "inspection_task",
        "executor",
    ).all().order_by("-performed_at", "-id")
    serializer_class = DeviceOperationRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_queryset_by_sales_scope(queryset, self.request.user, "project_device__project__sales_person_id")
        device_id = parse_query_int(self.request.query_params.get("device"))
        if device_id is not None:
            queryset = queryset.filter(device_id=device_id)
        record_type = self.request.query_params.get("record_type", "").strip()
        if record_type:
            queryset = queryset.filter(record_type=record_type)
        return queryset


class ProjectContractViewSet(SoftDeleteModelViewSet):
    queryset = ProjectContract.objects.select_related("project", "contract").all().order_by("id")
    serializer_class = ProjectContractSerializer


class ContractViewSet(SoftDeleteModelViewSet):
    queryset = Contract.objects.select_related("final_customer", "direct_buyer", "sales_person").all()
    serializer_class = ContractSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search_value = self.request.query_params.get("search", "").strip()
        queryset = filter_queryset_by_sales_scope(queryset, self.request.user, "sales_person_id")
        return apply_search(queryset, search_value, ["contract_no", "contract_name", "final_customer__name", "sales_person__name"])


class ContractDeviceViewSet(SoftDeleteModelViewSet):
    queryset = ContractDevice.objects.select_related("contract", "device").all()
    serializer_class = ContractDeviceSerializer


class ContractPartyViewSet(SoftDeleteModelViewSet):
    queryset = ContractParty.objects.select_related("contract", "organization").all()
    serializer_class = ContractPartySerializer


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def attachment_upload(request):
    serializer = AttachmentSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save(uploaded_by=request.user if request.user.is_authenticated else None)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer


def organization_summary(org):
    return {"id": org.id, "name": org.name, "org_type": org.org_type, "short_name": org.short_name, "region": org.region}


def person_summary(person):
    if not person:
        return None
    return {"id": person.id, "name": person.name, "person_type": person.person_type, "position": person.position, "phone": person.phone, "email": person.email}


def device_model_summary(model):
    if not model:
        return None
    product = getattr(model, "product", None)
    version = getattr(model, "product_version", None)
    return {
        "id": model.id,
        "model_name": model.model_name,
        "model_code": model.model_code,
        "product": model.product_id,
        "product_name": product.name if product else "",
        "product_version": model.product_version_id,
        "product_version_name": version.version_name if version else "",
    }


def device_summary(device, latest_binding=None):
    latest_binding = latest_binding or latest_project_device_service(device)
    latest_project = latest_binding.project if latest_binding else None
    return {
        "id": device.id,
        "name": device.name,
        "serial_number": device.serial_number,
        "device_model": device.device_model_id,
        "device_model_detail": device_model_summary(device.device_model),
        "hardware_code": device.hardware_code,
        "management_address": device.management_address,
        "version_update_method": device.version_update_method,
        "is_standard_product": device.is_standard_product,
        "nonstandard_name": device.nonstandard_name,
        "supports_remote": device.supports_remote,
        "software_version": device.software_version,
        "rule_library_version": device.rule_library_version,
        "license_info": device.license_info,
        "is_under_warranty": service_status_from_binding(latest_binding) == "\u4fdd\u5185",
        "current_service_status": service_status_from_binding(latest_binding),
        "current_service_start_date": latest_binding.service_start_date.isoformat() if latest_binding and latest_binding.service_start_date else None,
        "current_service_end_date": latest_binding.service_end_date.isoformat() if latest_binding and latest_binding.service_end_date else None,
        "service_overview": service_overview_for_binding(latest_binding),
        "current_signing_subject": latest_project.signing_subject if latest_project else "",
        "latest_project": {
            "id": latest_project.id,
            "project_no": latest_project.project_no,
            "name": latest_project.name,
        } if latest_project else None,
        "screenshot_url": device.screenshot_url,
        "rack_install_date": device.rack_install_date.isoformat() if device.rack_install_date else None,
        "ops_person": person_summary(device.ops_person),
        "remark": device.remark,
        "status": device.status,
    }


def contract_summary(contract):
    return {"id": contract.id, "contract_no": contract.contract_no, "contract_name": contract.contract_name, "amount": str(contract.amount), "status": contract.status}


def latest_project_device_service(device, customer=None):
    queryset = device.project_devices.filter(is_deleted=False, project__is_deleted=False).select_related("project")
    if customer:
        queryset = queryset.filter(project__customer_org=customer)
    return (
        queryset
        .order_by("-service_end_date", "-updated_at", "-id")
        .first()
    )


def customer_devices(customer):
    direct_devices = list(customer.devices.filter(is_deleted=False))
    related_project_devices = list(
        Device.objects.filter(
            project_devices__project__customer_org=customer,
            project_devices__is_deleted=False,
            is_deleted=False,
        ).distinct()
    )
    merged = {device.id: device for device in direct_devices}
    for device in related_project_devices:
        merged.setdefault(device.id, device)
    return list(merged.values())


def service_status_from_binding(binding):
    if not binding or not binding.service_start_date or not binding.service_end_date:
        return "\u4fdd\u5916"
    today = timezone.localdate()
    return "\u4fdd\u5185" if binding.service_start_date <= today <= binding.service_end_date else "\u4fdd\u5916"


def service_overview_for_binding(binding):
    if not binding:
        return None
    plan = binding.service_plans.filter(is_deleted=False).select_related("ops_person").order_by("-updated_at", "-id").first()
    if not plan:
        return None
    next_task = plan.inspection_tasks.filter(
        is_deleted=False,
        status__in=[InspectionTask.STATUS_PENDING, InspectionTask.STATUS_OVERDUE],
    ).order_by("planned_date", "id").first()
    return {
        "plan_id": plan.id,
        "inspection_frequency": plan.inspection_frequency,
        "reminder_days": plan.reminder_days,
        "service_contents": plan.service_contents,
        "ops_person": person_summary(plan.ops_person),
        "next_inspection_task": {
            "id": next_task.id,
            "planned_date": next_task.planned_date.isoformat(),
            "status": next_task.status,
        } if next_task else None,
    }


def project_device_summary(binding):
    return {
        **device_summary(binding.device),
        "id": binding.id,
        "device_id": binding.device_id,
        "project": binding.project_id,
        "quantity": binding.quantity,
        "deploy_location": binding.deploy_location,
        "device_project_type": binding.device_project_type,
        "usage": binding.usage,
        "service_type": binding.service_type,
        "service_start_date": binding.service_start_date.isoformat() if binding.service_start_date else None,
        "service_end_date": binding.service_end_date.isoformat() if binding.service_end_date else None,
        "offline_date": binding.offline_date.isoformat() if binding.offline_date else None,
        "service_status": service_status_from_binding(binding),
        "service_overview": service_overview_for_binding(binding),
    }


def project_summary(project):
    return {
        "id": project.id,
        "project_no": project.project_no,
        "name": project.name,
        "project_stage": project.project_stage,
        "signing_subject": project.signing_subject,
        "amount": str(project.amount),
        "customer_contact": person_summary(project.customer_contact),
        "sales_person": person_summary(project.sales_person),
    }


@api_view(["GET"])
def sales_customers(request, pk):
    sales_ids = get_user_sales_scope(request.user)
    if sales_ids is not None and pk not in sales_ids:
        return Response([], status=status.HTTP_200_OK)
    relations = SalesCustomerRelation.objects.filter(sales_person_id=pk, is_deleted=False).select_related("customer_org")
    payload = []
    for relation in relations:
        customer = relation.customer_org
        payload.append({
            **organization_summary(customer),
            "relation_type": relation.relation_type,
            "devices": [device_summary(device) for device in customer_devices(customer)],
            "contracts": [contract_summary(contract) for contract in customer.final_customer_contracts.all()],
        })
    return Response(payload)


@api_view(["GET", "POST"])
def sales_customer_relations(request, pk):
    sales = Person.objects.get(pk=pk)
    if request.method == "GET":
        relations = SalesCustomerRelation.objects.filter(sales_person=sales).select_related("customer_org")
        return Response({"customer_ids": [relation.customer_org_id for relation in relations], "customers": [organization_summary(relation.customer_org) for relation in relations]})

    customer_ids = request.data.get("customer_ids", [])
    SalesCustomerRelation.objects.filter(sales_person=sales).update(is_deleted=True)
    for customer_id in customer_ids:
        relation, _ = SalesCustomerRelation.all_objects.update_or_create(
            sales_person=sales,
            customer_org_id=customer_id,
            relation_type="owner",
            defaults={"is_deleted": False, "status": "active"},
        )
    return Response({"sales_id": sales.id, "customer_ids": customer_ids})


@api_view(["GET"])
def customer_overview(request, pk):
    customer = get_object_or_404(filter_customer_queryset_for_user(Organization.objects.all(), request.user), pk=pk)
    relations = customer.sales_relations.select_related("sales_person").all()
    return Response({
        "customer": organization_summary(customer),
        "contacts": [person_summary(person) for person in customer.people.filter(person_type="customer_contact")],
        "sales": [person_summary(relation.sales_person) for relation in relations],
        "devices": [device_summary(device) for device in customer_devices(customer)],
        "contracts": [contract_summary(contract) for contract in customer.final_customer_contracts.all()],
        "projects": [project_summary(project) for project in customer.projects.select_related("customer_contact", "sales_person").all()],
    })


@api_view(["GET"])
def device_overview(request, pk):
    device = get_object_or_404(filter_device_queryset_for_user(Device.objects.select_related("customer_org", "sales_person", "ops_person", "device_model__product", "device_model__product_version"), request.user), pk=pk)
    latest_binding = latest_project_device_service(device)
    latest_project = latest_binding.project if latest_binding else None
    customer_org = device.customer_org or (latest_project.customer_org if latest_project else None)
    sales_person = device.sales_person or (latest_project.sales_person if latest_project else None)
    customer_contact = latest_project.customer_contact if latest_project else None
    contracts = [binding.contract for binding in device.contract_devices.select_related("contract").all()]
    project_devices = device.project_devices.filter(is_deleted=False, project__is_deleted=False).select_related("project")
    return Response({
        "device": DeviceSerializer(device).data,
        "customer": organization_summary(customer_org) if customer_org else None,
        "customer_contact": person_summary(customer_contact),
        "sales_person": person_summary(sales_person),
        "ops_person": person_summary(device.ops_person),
        "contracts": [contract_summary(contract) for contract in contracts],
        "project_devices": [
            {
                "id": binding.id,
                "project_id": binding.project_id,
                "project_name": binding.project.name,
                "service_start_date": binding.service_start_date,
                "service_end_date": binding.service_end_date,
            }
            for binding in project_devices
        ],
        "attachments": AttachmentSerializer(Attachment.objects.filter(object_type="device", object_id=device.id), many=True, context={"request": request}).data,
    })


@api_view(["GET"])
def project_overview(request, pk):
    project = get_object_or_404(filter_queryset_by_sales_scope(Project.objects.select_related("customer_org", "customer_contact", "sales_person", "ops_person"), request.user, "sales_person_id"), pk=pk)
    bindings = project.project_devices.select_related("device", "device__device_model").all()
    project_contracts = project.project_contracts.select_related("contract").all()
    return Response({
        "project": ProjectSerializer(project).data,
        "customer": organization_summary(project.customer_org) if project.customer_org else None,
        "customer_contact": person_summary(project.customer_contact),
        "sales_person": person_summary(project.sales_person),
        "ops_person": person_summary(project.ops_person),
        "devices": [project_device_summary(binding) for binding in bindings],
        "contracts": [contract_summary(binding.contract) for binding in project_contracts],
        "attachments": AttachmentSerializer(Attachment.objects.filter(object_type="project", object_id=project.id), many=True, context={"request": request}).data,
    })


@api_view(["GET"])
def contract_overview(request, pk):
    contract = get_object_or_404(filter_queryset_by_sales_scope(Contract.objects.all(), request.user, "sales_person_id"), pk=pk)
    parties = contract.parties.select_related("organization").all()
    bindings = contract.contract_devices.select_related("device").all()
    return Response({
        "contract": ContractSerializer(contract).data,
        "parties": [{"id": party.id, "role": party.role, "order_index": party.order_index, "organization": organization_summary(party.organization)} for party in parties],
        "devices": [{**device_summary(binding.device), "quantity": binding.quantity, "price": str(binding.price)} for binding in bindings],
    })
