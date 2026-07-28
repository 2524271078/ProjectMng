from rest_framework import serializers

from django.db import transaction
from django.utils import timezone

from projects.models import Attachment, AuditLog, Contract, ContractDevice, ContractParty, Device, DeviceModel, DeviceOperationRecord, DeviceServicePlan, InspectionTask, Organization, Person, Product, ProductLine, ProductVersion, Project, ProjectContract, ProjectDevice, SalesCustomerRelation, ServiceStandardTemplate


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
    current_signing_subject = serializers.SerializerMethodField()
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

    def get_current_signing_subject(self, obj):
        project = self._latest_project(obj)
        return project.signing_subject if project else ''

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
    project_no = serializers.CharField(required=False, allow_blank=True)
    customer_org_detail = OrganizationSerializer(source='customer_org', read_only=True)
    customer_contact_detail = PersonSerializer(source='customer_contact', read_only=True)
    sales_person_detail = PersonSerializer(source='sales_person', read_only=True)
    ops_person_detail = PersonSerializer(source='ops_person', read_only=True)

    class Meta:
        model = Project
        fields = "__all__"

    def validate_project_no(self, value):
        project_no = value.strip()
        if self.instance and not project_no:
            raise serializers.ValidationError("项目编号不能为空")
        return project_no


class ProjectDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDevice
        fields = "__all__"


class ServiceStandardTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStandardTemplate
        fields = "__all__"

    def validate(self, attrs):
        frequency = attrs.get("inspection_frequency", getattr(self.instance, "inspection_frequency", ""))
        interval_days = attrs.get("inspection_interval_days", getattr(self.instance, "inspection_interval_days", None))
        if frequency == ServiceStandardTemplate.INSPECTION_CUSTOM and not interval_days:
            raise serializers.ValidationError({"inspection_interval_days": "自定义巡检频率必须填写巡检间隔天数"})
        return attrs


class DeviceServicePlanSerializer(serializers.ModelSerializer):
    project_device_detail = serializers.SerializerMethodField()
    template_detail = serializers.SerializerMethodField()
    ops_person_detail = serializers.SerializerMethodField()

    class Meta:
        model = DeviceServicePlan
        fields = "__all__"
        read_only_fields = ["standard_snapshot"]

    def get_project_device_detail(self, obj):
        binding = obj.project_device
        return {
            "id": binding.id,
            "project_id": binding.project_id,
            "project_name": binding.project.name,
            "device_id": binding.device_id,
            "service_start_date": binding.service_start_date,
            "service_end_date": binding.service_end_date,
        }

    def get_template_detail(self, obj):
        return {"id": obj.template_id, "name": obj.template.name} if obj.template else None

    def get_ops_person_detail(self, obj):
        return PersonSerializer(obj.ops_person).data if obj.ops_person else None

    def validate(self, attrs):
        template = attrs.get("template")
        frequency = attrs.get("inspection_frequency", getattr(self.instance, "inspection_frequency", template.inspection_frequency if template else ""))
        interval_days = attrs.get("inspection_interval_days", getattr(self.instance, "inspection_interval_days", template.inspection_interval_days if template else None))
        if frequency == ServiceStandardTemplate.INSPECTION_CUSTOM and not interval_days:
            raise serializers.ValidationError({"inspection_interval_days": "自定义巡检频率必须填写巡检间隔天数"})
        return attrs

    def create(self, validated_data):
        template = validated_data.get("template")
        if template:
            for field in ("inspection_frequency", "inspection_interval_days", "reminder_days", "auto_generate_tasks", "service_contents"):
                if field not in self.initial_data:
                    validated_data[field] = getattr(template, field)
            validated_data["standard_snapshot"] = {
                "template_id": template.id,
                "template_name": template.name,
                "inspection_frequency": validated_data["inspection_frequency"],
                "inspection_interval_days": validated_data["inspection_interval_days"],
                "reminder_days": validated_data["reminder_days"],
                "auto_generate_tasks": validated_data["auto_generate_tasks"],
                "service_contents": validated_data["service_contents"],
            }
        plan = super().create(validated_data)
        from projects.services import generate_inspection_tasks
        generate_inspection_tasks(plan)
        return plan


class InspectionTaskSerializer(serializers.ModelSerializer):
    service_plan_detail = serializers.SerializerMethodField()
    assignee_detail = PersonSerializer(source="assignee", read_only=True)

    class Meta:
        model = InspectionTask
        fields = "__all__"
        read_only_fields = ["reminder_sent_at", "completed_at"]

    def get_service_plan_detail(self, obj):
        plan = obj.service_plan
        return {"id": plan.id, "project_device": plan.project_device_id, "project_name": plan.project_device.project.name}


class DeviceOperationRecordSerializer(serializers.ModelSerializer):
    executor_detail = PersonSerializer(source="executor", read_only=True)

    class Meta:
        model = DeviceOperationRecord
        fields = "__all__"

    def validate(self, attrs):
        project_device = attrs.get("project_device", getattr(self.instance, "project_device", None))
        device = attrs.get("device", getattr(self.instance, "device", None))
        service_plan = attrs.get("service_plan", getattr(self.instance, "service_plan", None))
        task = attrs.get("inspection_task", getattr(self.instance, "inspection_task", None))
        record_type = attrs.get("record_type", getattr(self.instance, "record_type", None))
        if project_device and device and project_device.device_id != device.id:
            raise serializers.ValidationError({"device": "设备必须与项目设备一致"})
        if service_plan and project_device and service_plan.project_device_id != project_device.id:
            raise serializers.ValidationError({"service_plan": "服务计划必须属于当前项目设备"})
        if task and service_plan and task.service_plan_id != service_plan.id:
            raise serializers.ValidationError({"inspection_task": "巡检任务必须属于当前服务计划"})
        if task and record_type != DeviceOperationRecord.TYPE_INSPECTION:
            raise serializers.ValidationError({"record_type": "关联巡检任务时记录类型必须为巡检"})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        record = super().create(validated_data)
        update_fields = []
        if record.software_version_after:
            record.device.software_version = record.software_version_after
            update_fields.append("software_version")
        if record.rule_library_version_after:
            record.device.rule_library_version = record.rule_library_version_after
            update_fields.append("rule_library_version")
        if update_fields:
            record.device.save(update_fields=update_fields + ["updated_at"])
        if record.inspection_task_id:
            record.inspection_task.status = InspectionTask.STATUS_COMPLETED
            record.inspection_task.completed_at = record.performed_at or timezone.now()
            record.inspection_task.save(update_fields=["status", "completed_at", "updated_at"])
        return record


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
