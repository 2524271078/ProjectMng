from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, viewsets

from projects.models import Attachment, AuditLog, Contract, ContractDevice, ContractParty, Device, DeviceModel, Organization, Person, Product, ProductLine, ProductVersion, Project, ProjectContract, ProjectDevice, SalesCustomerRelation
from projects.serializers import AttachmentSerializer, AuditLogSerializer, ContractDeviceSerializer, ContractPartySerializer, ContractSerializer, DeviceModelSerializer, DeviceSerializer, OrganizationSerializer, PersonSerializer, ProductSerializer, ProductLineSerializer, ProductVersionSerializer, ProjectSerializer, ProjectContractSerializer, ProjectDeviceSerializer, SalesCustomerRelationSerializer


class SoftDeleteModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        model = queryset.model
        if any(field.name == "is_deleted" for field in model._meta.fields):
            queryset = queryset.filter(is_deleted=False)
        return queryset

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


class OrganizationViewSet(SoftDeleteModelViewSet):
    queryset = Organization.objects.all().order_by("id")
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search_value = self.request.query_params.get("search", "").strip()
        return apply_search(queryset, search_value, ["name", "region", "org_type"])


class PersonViewSet(SoftDeleteModelViewSet):
    queryset = Person.objects.select_related("organization", "user").all()
    serializer_class = PersonSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        person_type = self.request.query_params.get("person_type", "").strip()
        search_value = self.request.query_params.get("search", "").strip()
        if person_type:
            queryset = queryset.filter(person_type=person_type)
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
    queryset = Device.objects.select_related("device_model", "customer_org", "sales_person", "ops_person").all()
    serializer_class = DeviceSerializer


class ProjectViewSet(SoftDeleteModelViewSet):
    queryset = Project.objects.select_related("customer_org", "sales_person", "ops_person").all().order_by("id")
    serializer_class = ProjectSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search_value = self.request.query_params.get("search", "").strip()
        return apply_search(queryset, search_value, ["name", "customer_org__name", "sales_person__name", "project_stage"])


class ProjectDeviceViewSet(SoftDeleteModelViewSet):
    queryset = ProjectDevice.objects.select_related("project", "device").all().order_by("id")
    serializer_class = ProjectDeviceSerializer


class ProjectContractViewSet(SoftDeleteModelViewSet):
    queryset = ProjectContract.objects.select_related("project", "contract").all().order_by("id")
    serializer_class = ProjectContractSerializer


class ContractViewSet(SoftDeleteModelViewSet):
    queryset = Contract.objects.select_related("final_customer", "direct_buyer", "sales_person").all()
    serializer_class = ContractSerializer


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


def device_summary(device):
    latest_binding = latest_project_device_service(device)
    return {
        "id": device.id,
        "name": device.name,
        "serial_number": device.serial_number,
        "hardware_code": device.hardware_code,
        "management_address": device.management_address,
        "version_update_method": device.version_update_method,
        "is_standard_product": device.is_standard_product,
        "supports_remote": device.supports_remote,
        "software_version": device.software_version,
        "rule_library_version": device.rule_library_version,
        "license_info": device.license_info,
        "is_under_warranty": service_status_from_binding(latest_binding) == "保内",
        "current_service_status": service_status_from_binding(latest_binding),
        "current_service_start_date": latest_binding.service_start_date.isoformat() if latest_binding and latest_binding.service_start_date else None,
        "current_service_end_date": latest_binding.service_end_date.isoformat() if latest_binding and latest_binding.service_end_date else None,
        "screenshot_url": device.screenshot_url,
        "rack_install_date": device.rack_install_date.isoformat() if device.rack_install_date else None,
        "ops_person": person_summary(device.ops_person),
        "remark": device.remark,
        "status": device.status,
    }


def contract_summary(contract):
    return {"id": contract.id, "contract_no": contract.contract_no, "contract_name": contract.contract_name, "amount": str(contract.amount), "status": contract.status}


def latest_project_device_service(device):
    return (
        device.project_devices.filter(is_deleted=False)
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
        return "保外"
    today = timezone.localdate()
    return "保内" if binding.service_start_date <= today <= binding.service_end_date else "保外"


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
        "service_status": service_status_from_binding(binding),
    }


def project_summary(project):
    return {
        "id": project.id,
        "project_no": project.project_no,
        "name": project.name,
        "project_stage": project.project_stage,
        "amount": str(project.amount),
        "customer_contact": person_summary(project.customer_contact),
        "sales_person": person_summary(project.sales_person),
    }


@api_view(["GET"])
def sales_customers(request, pk):
    relations = SalesCustomerRelation.objects.filter(sales_person_id=pk).select_related("customer_org")
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
    customer = Organization.objects.get(pk=pk)
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
    device = Device.objects.select_related("customer_org", "sales_person", "ops_person", "device_model__product").get(pk=pk)
    contracts = [binding.contract for binding in device.contract_devices.select_related("contract").all()]
    return Response({
        "device": DeviceSerializer(device).data,
        "customer": organization_summary(device.customer_org) if device.customer_org else None,
        "sales_person": person_summary(device.sales_person),
        "ops_person": person_summary(device.ops_person),
        "contracts": [contract_summary(contract) for contract in contracts],
        "attachments": AttachmentSerializer(Attachment.objects.filter(object_type="device", object_id=device.id), many=True, context={"request": request}).data,
    })


@api_view(["GET"])
def project_overview(request, pk):
    project = Project.objects.select_related("customer_org", "customer_contact", "sales_person", "ops_person").get(pk=pk)
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
    contract = Contract.objects.get(pk=pk)
    parties = contract.parties.select_related("organization").all()
    bindings = contract.contract_devices.select_related("device").all()
    return Response({
        "contract": ContractSerializer(contract).data,
        "parties": [{"id": party.id, "role": party.role, "order_index": party.order_index, "organization": organization_summary(party.organization)} for party in parties],
        "devices": [{**device_summary(binding.device), "quantity": binding.quantity, "price": str(binding.price)} for binding in bindings],
    })
