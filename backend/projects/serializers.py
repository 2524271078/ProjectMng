from rest_framework import serializers

from projects.models import Attachment, AuditLog, Contract, ContractDevice, ContractParty, Device, DeviceModel, Organization, Person, Product, ProductLine, ProductVersion, Project, ProjectContract, ProjectDevice, SalesCustomerRelation


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = "__all__"


class SalesCustomerRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesCustomerRelation
        fields = "__all__"


class ProductLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLine
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class ProductVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVersion
        fields = "__all__"


class DeviceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceModel
        fields = "__all__"


class DeviceSerializer(serializers.ModelSerializer):
    current_service_status = serializers.SerializerMethodField()
    current_service_start_date = serializers.SerializerMethodField()
    current_service_end_date = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = "__all__"

    def _latest_binding(self, obj):
        return (
            obj.project_devices.filter(is_deleted=False)
            .order_by("-service_end_date", "-updated_at", "-id")
            .first()
        )

    def get_current_service_status(self, obj):
        binding = self._latest_binding(obj)
        if not binding or not binding.service_start_date or not binding.service_end_date:
            return "保外"
        from django.utils import timezone
        today = timezone.localdate()
        return "保内" if binding.service_start_date <= today <= binding.service_end_date else "保外"

    def get_current_service_start_date(self, obj):
        binding = self._latest_binding(obj)
        return binding.service_start_date.isoformat() if binding and binding.service_start_date else None

    def get_current_service_end_date(self, obj):
        binding = self._latest_binding(obj)
        return binding.service_end_date.isoformat() if binding and binding.service_end_date else None


class ProjectSerializer(serializers.ModelSerializer):
    customer_org_detail = OrganizationSerializer(source="customer_org", read_only=True)
    customer_contact_detail = PersonSerializer(source="customer_contact", read_only=True)
    sales_person_detail = PersonSerializer(source="sales_person", read_only=True)
    ops_person_detail = PersonSerializer(source="ops_person", read_only=True)

    class Meta:
        model = Project
        fields = "__all__"


class ProjectDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDevice
        fields = "__all__"


class ProjectContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContract
        fields = "__all__"


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = "__all__"


class ContractDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractDevice
        fields = "__all__"


class ContractPartySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractParty
        fields = "__all__"


class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = "__all__"

    def get_file_url(self, obj):
        if not obj.file:
            return ""
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"
