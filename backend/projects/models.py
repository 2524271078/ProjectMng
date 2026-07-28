from django.conf import settings
from django.db import models

from core.models import BaseModel


class Organization(BaseModel):
    name = models.CharField(max_length=200, db_index=True)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.SET_NULL)
    org_type = models.CharField(max_length=64, db_index=True)
    short_name = models.CharField(max_length=100, blank=True, default="")
    region = models.CharField(max_length=100, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["org_type", "name"])]

    def __str__(self):
        return self.short_name or self.name


class Person(BaseModel):
    name = models.CharField(max_length=100, db_index=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, related_name="people", on_delete=models.SET_NULL)
    person_type = models.CharField(max_length=64, db_index=True)
    position = models.CharField(max_length=100, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    wechat = models.CharField(max_length=100, blank=True, default="")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="person_profile", on_delete=models.SET_NULL)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["person_type", "name"])]

    def __str__(self):
        return self.name


class SalesCustomerRelation(BaseModel):
    sales_person = models.ForeignKey(Person, related_name="sales_customer_relations", on_delete=models.PROTECT)
    customer_org = models.ForeignKey(Organization, related_name="sales_relations", on_delete=models.PROTECT)
    relation_type = models.CharField(max_length=64, default="owner", db_index=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["sales_person", "customer_org", "status"])]
        constraints = [
            models.UniqueConstraint(
                fields=["sales_person", "customer_org", "relation_type"],
                condition=models.Q(is_deleted=False),
                name="uniq_active_sales_customer_relation",
            )
        ]


class ProductLine(BaseModel):
    name = models.CharField(max_length=200, db_index=True)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name


class Product(BaseModel):
    product_line = models.ForeignKey(ProductLine, null=True, blank=True, related_name="products", on_delete=models.SET_NULL)
    name = models.CharField(max_length=200, db_index=True)
    product_code = models.CharField(max_length=100, blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default="")
    manufacturer = models.ForeignKey(Organization, null=True, blank=True, related_name="products", on_delete=models.SET_NULL)
    description = models.TextField(blank=True, default="")

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['product_code'],
                condition=models.Q(is_deleted=False) & ~models.Q(product_code=''),
                name='uniq_active_product_code',
            )
        ]

    def __str__(self):
        return self.name


class ProductVersion(BaseModel):
    product = models.ForeignKey(Product, related_name="versions", on_delete=models.CASCADE)
    version_name = models.CharField(max_length=100, db_index=True)
    version_code = models.CharField(max_length=100, blank=True, default='')
    release_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, default="")

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'version_code'],
                condition=models.Q(is_deleted=False) & ~models.Q(version_code=''),
                name="uniq_active_product_version",
            )
        ]

    def __str__(self):
        return f"{self.product.name} {self.version_name}"


class DeviceModel(BaseModel):
    product = models.ForeignKey(Product, related_name="device_models", on_delete=models.PROTECT)
    product_version = models.ForeignKey(ProductVersion, null=True, blank=True, related_name="device_models", on_delete=models.SET_NULL)
    model_name = models.CharField(max_length=200, db_index=True)
    model_code = models.CharField(max_length=100, blank=True, default='')
    manufacturer = models.ForeignKey(Organization, null=True, blank=True, related_name="device_models", on_delete=models.SET_NULL)
    description = models.TextField(blank=True, default="")

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['model_code'],
                condition=models.Q(is_deleted=False) & ~models.Q(model_code=''),
                name='uniq_active_model_code',
            )
        ]

    def __str__(self):
        return self.model_name


class Device(BaseModel):
    name = models.CharField(max_length=200, db_index=True)
    serial_number = models.CharField(max_length=100, unique=True)
    device_model = models.ForeignKey(DeviceModel, related_name="devices", on_delete=models.PROTECT)
    hardware_code = models.CharField(max_length=100, blank=True, default="")
    management_address = models.CharField(max_length=255, blank=True, default="")
    version_update_method = models.CharField(max_length=100, blank=True, default="")
    is_standard_product = models.BooleanField(default=True, db_index=True)
    nonstandard_name = models.CharField(max_length=200, blank=True, default='')
    supports_remote = models.BooleanField(default=False, db_index=True)
    software_version = models.CharField(max_length=100, blank=True, default="")
    rule_library_version = models.CharField(max_length=100, blank=True, default="")
    license_info = models.JSONField(default=dict, blank=True)
    is_under_warranty = models.BooleanField(default=False, db_index=True)
    screenshot_url = models.URLField(blank=True, default="")
    license_expire_date = models.DateField(null=True, blank=True)
    rack_install_date = models.DateField(null=True, blank=True)
    online_date = models.DateField(null=True, blank=True)
    offline_date = models.DateField(null=True, blank=True)
    customer_org = models.ForeignKey(Organization, null=True, blank=True, related_name="devices", on_delete=models.SET_NULL)
    sales_person = models.ForeignKey(Person, null=True, blank=True, related_name="sold_devices", on_delete=models.SET_NULL)
    ops_person = models.ForeignKey(Person, null=True, blank=True, related_name="ops_devices", on_delete=models.SET_NULL)
    basic_info_image = models.ImageField(upload_to="devices/basic/", blank=True, default="")

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["customer_org", "sales_person", "status"])]

    def __str__(self):
        return self.name


class Project(BaseModel):
    SIGNING_SUBJECT_DIRECT = "direct"
    SIGNING_SUBJECT_AGENT = "agent"
    SIGNING_SUBJECT_CHOICES = [
        (SIGNING_SUBJECT_DIRECT, "直签"),
        (SIGNING_SUBJECT_AGENT, "代理"),
    ]

    project_no = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200, db_index=True)
    customer_org = models.ForeignKey(Organization, null=True, blank=True, related_name="projects", on_delete=models.SET_NULL)
    customer_contact = models.ForeignKey(Person, null=True, blank=True, related_name="customer_projects", on_delete=models.SET_NULL)
    winning_company = models.CharField(max_length=200, blank=True, default="")
    contact_company = models.CharField(max_length=200, blank=True, default="")
    signing_subject = models.CharField(max_length=16, choices=SIGNING_SUBJECT_CHOICES, default=SIGNING_SUBJECT_DIRECT, db_index=True)
    sales_person = models.ForeignKey(Person, null=True, blank=True, related_name="sales_projects", on_delete=models.SET_NULL)
    ops_person = models.ForeignKey(Person, null=True, blank=True, related_name="ops_projects", on_delete=models.SET_NULL)
    project_stage = models.CharField(max_length=64, blank=True, default="new", db_index=True)
    sign_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["customer_org", "sales_person", "project_stage", "signing_subject", "status"])]

    def __str__(self):
        return self.name


class ProjectDevice(BaseModel):
    SERVICE_NEW_INSTALL = "new_install"
    SERVICE_RENEWAL = "renewal"
    SERVICE_OFFLINE = "offline"
    SERVICE_TYPE_CHOICES = [
        (SERVICE_NEW_INSTALL, "\u65b0\u4e0a\u8bbe\u5907"),
        (SERVICE_RENEWAL, "\u7eed\u4fdd\u65e7\u8bbe\u5907"),
        (SERVICE_OFFLINE, "\u4e0b\u67b6"),
    ]

    project = models.ForeignKey(Project, related_name="project_devices", on_delete=models.CASCADE)
    device = models.ForeignKey(Device, related_name="project_devices", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    deploy_location = models.CharField(max_length=200, blank=True, default="")
    device_project_type = models.CharField(max_length=100, blank=True, default="")
    usage = models.CharField(max_length=200, blank=True, default="")
    service_type = models.CharField(max_length=32, default=SERVICE_NEW_INSTALL, choices=SERVICE_TYPE_CHOICES, db_index=True)
    service_start_date = models.DateField(null=True, blank=True)
    service_end_date = models.DateField(null=True, blank=True)
    offline_date = models.DateField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["project", "device"],
                condition=models.Q(is_deleted=False),
                name="uniq_active_project_device",
            )
        ]


class ServiceStandardTemplate(BaseModel):
    """可复用的设备服务标准，例如“标准维保（季度巡检）”。"""

    INSPECTION_MONTHLY = "monthly"
    INSPECTION_QUARTERLY = "quarterly"
    INSPECTION_SEMIANNUAL = "semiannual"
    INSPECTION_ANNUAL = "annual"
    INSPECTION_CUSTOM = "custom"
    INSPECTION_FREQUENCY_CHOICES = [
        (INSPECTION_MONTHLY, "每月"),
        (INSPECTION_QUARTERLY, "每季度"),
        (INSPECTION_SEMIANNUAL, "每半年"),
        (INSPECTION_ANNUAL, "每年"),
        (INSPECTION_CUSTOM, "自定义天数"),
    ]

    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=50, blank=True, default="")
    inspection_frequency = models.CharField(max_length=20, choices=INSPECTION_FREQUENCY_CHOICES, default=INSPECTION_QUARTERLY)
    inspection_interval_days = models.PositiveIntegerField(null=True, blank=True)
    reminder_days = models.PositiveIntegerField(default=7)
    auto_generate_tasks = models.BooleanField(default=True)
    service_contents = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True, default="")

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=models.Q(is_deleted=False) & ~models.Q(code=""),
                name="uniq_active_service_standard_code",
            )
        ]

    def __str__(self):
        return self.name


class DeviceServicePlan(BaseModel):
    """设备在一段项目服务周期内生效的服务标准快照。"""

    project_device = models.ForeignKey(ProjectDevice, related_name="service_plans", on_delete=models.CASCADE)
    template = models.ForeignKey(ServiceStandardTemplate, null=True, blank=True, related_name="device_service_plans", on_delete=models.SET_NULL)
    inspection_frequency = models.CharField(max_length=20, choices=ServiceStandardTemplate.INSPECTION_FREQUENCY_CHOICES, default=ServiceStandardTemplate.INSPECTION_QUARTERLY)
    inspection_interval_days = models.PositiveIntegerField(null=True, blank=True)
    first_inspection_date = models.DateField(null=True, blank=True)
    reminder_days = models.PositiveIntegerField(default=7)
    auto_generate_tasks = models.BooleanField(default=True)
    service_contents = models.JSONField(default=list, blank=True)
    standard_snapshot = models.JSONField(default=dict, blank=True)
    ops_person = models.ForeignKey(Person, null=True, blank=True, related_name="device_service_plans", on_delete=models.SET_NULL)
    remark = models.TextField(blank=True, default="")

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["project_device", "status"])]
        constraints = [
            models.UniqueConstraint(
                fields=["project_device"],
                condition=models.Q(is_deleted=False),
                name="uniq_active_project_device_service_plan",
            )
        ]


class InspectionTask(BaseModel):
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_OVERDUE = "overdue"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "待巡检"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_OVERDUE, "已逾期"),
        (STATUS_CANCELLED, "已取消"),
    ]

    service_plan = models.ForeignKey(DeviceServicePlan, related_name="inspection_tasks", on_delete=models.CASCADE)
    planned_date = models.DateField(db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    assignee = models.ForeignKey(Person, null=True, blank=True, related_name="inspection_tasks", on_delete=models.SET_NULL)
    reminder_date = models.DateField(null=True, blank=True, db_index=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    remark = models.TextField(blank=True, default="")

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["status", "planned_date"])]
        constraints = [
            models.UniqueConstraint(
                fields=["service_plan", "planned_date"],
                condition=models.Q(is_deleted=False),
                name="uniq_active_inspection_task_date",
            )
        ]


class DeviceOperationRecord(BaseModel):
    TYPE_INSPECTION = "inspection"
    TYPE_SYSTEM_UPGRADE = "system_upgrade"
    TYPE_RULE_LIBRARY_UPGRADE = "rule_library_upgrade"
    TYPE_FAULT_HANDLING = "fault_handling"
    TYPE_CONFIGURATION_CHANGE = "configuration_change"
    TYPE_TECHNICAL_SUPPORT = "technical_support"
    TYPE_OTHER = "other"
    RECORD_TYPE_CHOICES = [
        (TYPE_INSPECTION, "巡检"),
        (TYPE_SYSTEM_UPGRADE, "系统升级"),
        (TYPE_RULE_LIBRARY_UPGRADE, "规则库升级"),
        (TYPE_FAULT_HANDLING, "故障处理"),
        (TYPE_CONFIGURATION_CHANGE, "配置变更"),
        (TYPE_TECHNICAL_SUPPORT, "技术支持"),
        (TYPE_OTHER, "其他"),
    ]
    RESULT_NORMAL = "normal"
    RESULT_ISSUE_FOUND = "issue_found"
    RESULT_FOLLOW_UP = "follow_up"
    RESULT_CHOICES = [
        (RESULT_NORMAL, "正常"),
        (RESULT_ISSUE_FOUND, "发现问题"),
        (RESULT_FOLLOW_UP, "需跟进"),
    ]

    device = models.ForeignKey(Device, related_name="operation_records", on_delete=models.PROTECT)
    project_device = models.ForeignKey(ProjectDevice, related_name="operation_records", on_delete=models.PROTECT)
    service_plan = models.ForeignKey(DeviceServicePlan, null=True, blank=True, related_name="operation_records", on_delete=models.SET_NULL)
    inspection_task = models.OneToOneField(InspectionTask, null=True, blank=True, related_name="operation_record", on_delete=models.SET_NULL)
    record_type = models.CharField(max_length=32, choices=RECORD_TYPE_CHOICES, db_index=True)
    performed_at = models.DateTimeField(db_index=True)
    executor = models.ForeignKey(Person, null=True, blank=True, related_name="operation_records", on_delete=models.SET_NULL)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default=RESULT_NORMAL)
    check_items = models.JSONField(default=list, blank=True)
    issue_description = models.TextField(blank=True, default="")
    resolution = models.TextField(blank=True, default="")
    follow_up_date = models.DateField(null=True, blank=True)
    software_version_before = models.CharField(max_length=100, blank=True, default="")
    software_version_after = models.CharField(max_length=100, blank=True, default="")
    rule_library_version_before = models.CharField(max_length=100, blank=True, default="")
    rule_library_version_after = models.CharField(max_length=100, blank=True, default="")
    attachment_urls = models.JSONField(default=list, blank=True)
    customer_confirmed_by = models.CharField(max_length=100, blank=True, default="")
    customer_confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["device", "performed_at"]),
            models.Index(fields=["project_device", "record_type", "performed_at"]),
        ]


class Contract(BaseModel):
    contract_no = models.CharField(max_length=100, unique=True)
    contract_name = models.CharField(max_length=200, db_index=True)
    final_customer = models.ForeignKey(Organization, null=True, blank=True, related_name="final_customer_contracts", on_delete=models.SET_NULL)
    direct_buyer = models.ForeignKey(Organization, null=True, blank=True, related_name="direct_buyer_contracts", on_delete=models.SET_NULL)
    sales_person = models.ForeignKey(Person, null=True, blank=True, related_name="contracts", on_delete=models.SET_NULL)
    sign_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["final_customer", "sales_person", "status"])]

    def __str__(self):
        return self.contract_name


class ProjectContract(BaseModel):
    project = models.ForeignKey(Project, related_name="project_contracts", on_delete=models.CASCADE)
    contract = models.ForeignKey(Contract, related_name="project_contracts", on_delete=models.PROTECT)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["project", "contract"],
                condition=models.Q(is_deleted=False),
                name="uniq_active_project_contract",
            )
        ]


class ContractDevice(BaseModel):
    contract = models.ForeignKey(Contract, related_name="contract_devices", on_delete=models.CASCADE)
    device = models.ForeignKey(Device, related_name="contract_devices", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["contract", "device"],
                condition=models.Q(is_deleted=False),
                name="uniq_active_contract_device",
            )
        ]


class ContractParty(BaseModel):
    contract = models.ForeignKey(Contract, related_name="parties", on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name="contract_parties", on_delete=models.PROTECT)
    role = models.CharField(max_length=64, db_index=True)
    order_index = models.PositiveIntegerField(default=0)

    class Meta(BaseModel.Meta):
        ordering = ["order_index", "id"]
        indexes = [models.Index(fields=["contract", "order_index"])]


class Attachment(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to="attachments/", blank=True, default="")
    object_type = models.CharField(max_length=100, db_index=True)
    object_id = models.PositiveBigIntegerField(db_index=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="uploaded_attachments", on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    remark = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["object_type", "object_id"])]

    def __str__(self):
        return self.name


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="audit_logs", on_delete=models.SET_NULL)
    action = models.CharField(max_length=64, db_index=True)
    object_type = models.CharField(max_length=100, db_index=True)
    object_id = models.PositiveBigIntegerField(db_index=True)
    before_data = models.JSONField(default=dict, blank=True)
    after_data = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["object_type", "object_id", "action"])]
