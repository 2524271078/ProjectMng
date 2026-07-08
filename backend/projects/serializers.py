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
    service_type = serializers.SerializerMethodField()
    deploy_location = serializers.SerializerMethodField()
    offline_date = serializers.SerializerMethodField()
    customer_org_detail = serializers.SerializerMethodField()
    customer_contact_detail = serializers.SerializerMethodField()
    sales_person_detail = serializers.SerializerMethodField()
    device_model_detail = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = "__all__"

    def _latest_binding(self, obj):
        if hasattr(obj, '_latest_active_project_binding_cached'):
            return obj._latest_active_project_binding_cached
        obj._latest_active_project_binding_cached = (
            obj.project_devices.select_related('project__customer_org', 'project__customer_contact', 'project__sales_person')
            .filter(is_deleted=False)
            .order_by('-service_end_date', '-updated_at', '-id')
            .first()
        )
        return obj._latest_active_project_binding_cached

    def _latest_project(self, obj):
        binding = self._latest_binding(obj)
        return binding.project if binding else None

    def get_current_service_status(self, obj):
        binding = self._latest_binding(obj)
        if not binding or not binding.service_start_date or not binding.service_end_date:
            return '保外'
        from django.utils import timezone
        today = timezone.localdate()
        return '保内' if binding.service_start_date <= today <= binding.service_end_date else '保外'

    def get_current_service_start_date(self, obj):
        binding = self._latest_binding(obj)
        return binding.service_start_date.isoformat() if binding and binding.service_start_date else None

    def get_current_service_end_date(self, obj):
        binding = self._latest_binding(obj)
        return binding.service_end_date.isoformat() if binding and binding.service_end_date else None

    def get_service_type(self, obj):
        binding = self._latest_binding(obj)
        return binding.service_type if binding else ''

    def get_deploy_location(self, obj):
        binding = self._latest_binding(obj)
        return binding.deploy_location if binding else ''

    def get_offline_date(self, obj):
        binding = self._latest_binding(obj)
        return binding.offline_date.isoformat() if binding and binding.offline_date else None

    def get_customer_org_detail(self, obj):
        project = self._latest_project(obj)
        organization = obj.customer_org or (project.customer_org if project else None)
        return OrganizationSerializer(organization).data if organization else None

    def get_customer_contact_detail(self, obj):
        project = self._latest_project(obj)
        person = project.customer_contact if project else None
        return PersonSerializer(person).data if person else None

    def get_sales_person_detail(self, obj):
        project = self._latest_project(obj)
        person = obj.sales_person or (project.sales_person if project else None)
        return PersonSerializer(person).data if person else None

    def get_device_model_detail(self, obj):
        model = obj.device_model
        if not model:
            return None
        product = getattr(model, 'product', None)
        version = getattr(model, 'product_version', None)
        return {
            'id': model.id,
            'model_name': model.model_name,
            'model_code': model.model_code,
            'product': model.product_id,
            'product_name': product.name if product else '',
            'product_version': model.product_version_id,
            'product_version_name': version.version_name if version else '',
        }


class ProjectSerializer(serializers.ModelSerializer):
    customer_org_detail = OrganizationSerializer(source='customer_org', read_only=True)
    customer_contact_detail = PersonSerializer(source='customer_contact', read_only=True)
    sales_person_detail = PersonSerializer(source='sales_person', read_only=True)
    ops_person_detail = PersonSerializer(source='ops_person', read_only=True)

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
        request = self.context.get('request')
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"
