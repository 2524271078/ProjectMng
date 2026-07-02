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


class Product(BaseModel):
    name = models.CharField(max_length=200, db_index=True)
    product_code = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, default="")
    manufacturer = models.ForeignKey(Organization, null=True, blank=True, related_name="products", on_delete=models.SET_NULL)
    description = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name


class DeviceModel(BaseModel):
    product = models.ForeignKey(Product, related_name="device_models", on_delete=models.PROTECT)
    model_name = models.CharField(max_length=200, db_index=True)
    model_code = models.CharField(max_length=100, unique=True)
    manufacturer = models.ForeignKey(Organization, null=True, blank=True, related_name="device_models", on_delete=models.SET_NULL)
    description = models.TextField(blank=True, default="")

    def __str__(self):
        return self.model_name


class Device(BaseModel):
    name = models.CharField(max_length=200, db_index=True)
    serial_number = models.CharField(max_length=100, unique=True)
    device_model = models.ForeignKey(DeviceModel, related_name="devices", on_delete=models.PROTECT)
    hardware_code = models.CharField(max_length=100, blank=True, default="")
    software_version = models.CharField(max_length=100, blank=True, default="")
    rule_library_version = models.CharField(max_length=100, blank=True, default="")
    license_info = models.JSONField(default=dict, blank=True)
    license_expire_date = models.DateField(null=True, blank=True)
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
