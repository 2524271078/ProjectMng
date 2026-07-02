from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets

from projects.models import Attachment, AuditLog, Contract, ContractDevice, ContractParty, Device, DeviceModel, Organization, Person, Product, SalesCustomerRelation
from projects.serializers import AttachmentSerializer, AuditLogSerializer, ContractDeviceSerializer, ContractPartySerializer, ContractSerializer, DeviceModelSerializer, DeviceSerializer, OrganizationSerializer, PersonSerializer, ProductSerializer, SalesCustomerRelationSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.select_related("organization", "user").all()
    serializer_class = PersonSerializer


class SalesCustomerRelationViewSet(viewsets.ModelViewSet):
    queryset = SalesCustomerRelation.objects.select_related("sales_person", "customer_org").all()
    serializer_class = SalesCustomerRelationSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("manufacturer").all()
    serializer_class = ProductSerializer


class DeviceModelViewSet(viewsets.ModelViewSet):
    queryset = DeviceModel.objects.select_related("product", "manufacturer").all()
    serializer_class = DeviceModelSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.select_related("device_model", "customer_org", "sales_person", "ops_person").all()
    serializer_class = DeviceSerializer


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.select_related("final_customer", "direct_buyer", "sales_person").all()
    serializer_class = ContractSerializer


class ContractDeviceViewSet(viewsets.ModelViewSet):
    queryset = ContractDevice.objects.select_related("contract", "device").all()
    serializer_class = ContractDeviceSerializer


class ContractPartyViewSet(viewsets.ModelViewSet):
    queryset = ContractParty.objects.select_related("contract", "organization").all()
    serializer_class = ContractPartySerializer


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer


def organization_summary(org):
    return {"id": org.id, "name": org.name, "org_type": org.org_type, "short_name": org.short_name, "region": org.region}


def person_summary(person):
    if not person:
        return None
    return {"id": person.id, "name": person.name, "person_type": person.person_type, "phone": person.phone, "email": person.email}


def device_summary(device):
    return {"id": device.id, "name": device.name, "serial_number": device.serial_number, "status": device.status}


def contract_summary(contract):
    return {"id": contract.id, "contract_no": contract.contract_no, "contract_name": contract.contract_name, "amount": str(contract.amount), "status": contract.status}


@api_view(["GET"])
def sales_customers(request, pk):
    relations = SalesCustomerRelation.objects.filter(sales_person_id=pk).select_related("customer_org")
    payload = []
    for relation in relations:
        customer = relation.customer_org
        payload.append({
            **organization_summary(customer),
            "relation_type": relation.relation_type,
            "devices": [device_summary(device) for device in customer.devices.all()],
            "contracts": [contract_summary(contract) for contract in customer.final_customer_contracts.all()],
        })
    return Response(payload)


@api_view(["GET"])
def customer_overview(request, pk):
    customer = Organization.objects.get(pk=pk)
    relations = customer.sales_relations.select_related("sales_person").all()
    return Response({
        "customer": organization_summary(customer),
        "contacts": [person_summary(person) for person in customer.people.filter(person_type="customer_contact")],
        "sales": [person_summary(relation.sales_person) for relation in relations],
        "devices": [device_summary(device) for device in customer.devices.all()],
        "contracts": [contract_summary(contract) for contract in customer.final_customer_contracts.all()],
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
        "attachments": AttachmentSerializer(Attachment.objects.filter(object_type="device", object_id=device.id), many=True).data,
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
