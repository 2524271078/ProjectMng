from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APITestCase

from projects.models import (
    Attachment,
    AuditLog,
    Contract,
    ContractDevice,
    ContractParty,
    Device,
    DeviceModel,
    Organization,
    Person,
    Product,
    SalesCustomerRelation,
)


class DomainModelTests(TestCase):
    def test_project_purchase_workflow_relationships_can_be_created(self):
        internal = Organization.objects.create(name="盛邦安全", org_type="internal_company")
        customer = Organization.objects.create(name="华东客户", org_type="customer", region="华东")
        integrator = Organization.objects.create(name="集成商 A", org_type="integrator")
        manufacturer = Organization.objects.create(name="厂商 A", org_type="vendor")

        sales = Person.objects.create(name="销售一", organization=internal, person_type="sales")
        ops = Person.objects.create(name="运维一", organization=internal, person_type="ops")
        contact = Person.objects.create(name="客户联系人", organization=customer, person_type="customer_contact")

        relation = SalesCustomerRelation.objects.create(
            sales_person=sales,
            customer_org=customer,
            relation_type="owner",
            start_date=date(2026, 1, 1),
        )

        product = Product.objects.create(name="安全网关", product_code="SG", manufacturer=manufacturer)
        model = DeviceModel.objects.create(
            product=product,
            model_name="SG-1000",
            model_code="SG1000",
            manufacturer=manufacturer,
        )
        device = Device.objects.create(
            name="华东客户网关 01",
            serial_number="SN-001",
            device_model=model,
            customer_org=customer,
            sales_person=sales,
            ops_person=ops,
            license_info={"type": "standard"},
            extra={"rack": "A01"},
        )
        contract = Contract.objects.create(
            contract_no="HT-2026-001",
            contract_name="华东客户安全网关采购",
            final_customer=customer,
            direct_buyer=integrator,
            sales_person=sales,
            sign_date=date(2026, 2, 1),
            amount=Decimal("100000.00"),
        )
        ContractParty.objects.create(contract=contract, organization=customer, role="final_customer", order_index=1)
        ContractParty.objects.create(contract=contract, organization=integrator, role="direct_buyer", order_index=2)
        binding = ContractDevice.objects.create(contract=contract, device=device, quantity=1, price=Decimal("88000.00"))

        self.assertEqual(relation.sales_person, sales)
        self.assertEqual(contact.organization, customer)
        self.assertEqual(device.customer_org, customer)
        self.assertEqual(device.sales_person, sales)
        self.assertEqual(contract.parties.count(), 2)
        self.assertEqual(binding.device.device_model.product, product)
        self.assertEqual(device.extra["rack"], "A01")

    def test_required_business_models_keep_common_extension_fields(self):
        models = [
            Organization,
            Person,
            SalesCustomerRelation,
            Product,
            DeviceModel,
            Device,
            Contract,
            ContractDevice,
            ContractParty,
        ]

        for model in models:
            field_names = {field.name for field in model._meta.fields}
            self.assertIn("remark", field_names, model.__name__)
            self.assertIn("status", field_names, model.__name__)
            self.assertIn("extra", field_names, model.__name__)
            self.assertIn("created_at", field_names, model.__name__)
            self.assertIn("updated_at", field_names, model.__name__)
            self.assertIn("created_by", field_names, model.__name__)
            self.assertIn("updated_by", field_names, model.__name__)
            self.assertIn("is_deleted", field_names, model.__name__)

    def test_attachment_and_audit_log_models_exist_for_upload_and_traceability(self):
        attachment = Attachment.objects.create(name="设备图片", object_type="device", object_id=1)
        log = AuditLog.objects.create(action="create", object_type="device", object_id=1, after_data={"name": "设备"})

        self.assertEqual(attachment.object_type, "device")
        self.assertEqual(log.after_data["name"], "设备")


class PersonApiValidationTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="person-api", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_person_can_be_created_without_organization(self):
        response = self.client.post("/api/people/", {"name": "临时联系人", "person_type": "customer_contact"}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "临时联系人")
        self.assertIsNone(response.data["organization"])


class StateGridImportCommandTests(TestCase):
    def test_command_resets_and_imports_state_grid_organization_tree(self):
        from django.core.management import call_command
        from projects.models import Organization

        Organization.objects.create(name="旧组织", org_type="customer")

        call_command("reset_state_grid_orgs", yes=True, verbosity=0)

        self.assertFalse(Organization.objects.filter(name="旧组织").exists())
        root = Organization.objects.get(name="国网电力公司")
        self.assertTrue(root.children.filter(name="国网天津电力").exists())
        branches = Organization.objects.get(name="国网六大分部")
        self.assertEqual(branches.children.count(), 6)
        affiliates = Organization.objects.get(name="国网三产公司")
        self.assertTrue(affiliates.children.filter(name="国网英大").exists())


class SoftDeleteApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="soft-delete", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_organization_delete_marks_row_deleted_and_hides_from_list(self):
        org = Organization.objects.create(name="待删除客户", org_type="customer")

        response = self.client.delete(f"/api/organizations/{org.id}/")

        self.assertEqual(response.status_code, 204)
        org.refresh_from_db()
        self.assertTrue(org.is_deleted)
        list_response = self.client.get("/api/organizations/")
        names = [item["name"] for item in list_response.data]
        self.assertNotIn("待删除客户", names)


class ProductProjectModelTests(TestCase):
    def test_product_line_version_model_and_project_device_flow(self):
        from decimal import Decimal
        from projects.models import Project, ProjectDevice, ProductLine, ProductVersion

        customer = Organization.objects.create(name="项目客户", org_type="customer")
        internal = Organization.objects.create(name="内部公司", org_type="internal_company")
        sales = Person.objects.create(name="项目销售", organization=internal, person_type="sales")
        ops = Person.objects.create(name="项目运维", organization=internal, person_type="ops")
        vendor = Organization.objects.create(name="产品厂商", org_type="vendor")

        line = ProductLine.objects.create(name="边界安全产线", code="EDGE")
        product = Product.objects.create(name="下一代防火墙", product_code="NGFW", product_line=line, manufacturer=vendor)
        version = ProductVersion.objects.create(product=product, version_name="V5.0", version_code="5.0")
        model = DeviceModel.objects.create(product=product, product_version=version, model_name="SG-3000", model_code="SG3000", manufacturer=vendor)
        device = Device.objects.create(name="项目防火墙", serial_number="P-SN-001", device_model=model)
        project = Project.objects.create(
            project_no="PRJ-2026-001",
            name="国网安全建设项目",
            customer_org=customer,
            sales_person=sales,
            ops_person=ops,
            project_stage="delivery",
            amount=Decimal("120000.00"),
        )
        binding = ProjectDevice.objects.create(project=project, device=device, quantity=2, deploy_location="主机房")
        Attachment.objects.create(name="合同扫描件", object_type="project", object_id=project.id)

        self.assertEqual(product.product_line, line)
        self.assertEqual(model.product_version, version)
        self.assertEqual(binding.project.customer_org, customer)
        self.assertEqual(project.project_devices.count(), 1)
        self.assertEqual(Attachment.objects.filter(object_type="project", object_id=project.id).count(), 1)


class ProjectApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="project-api", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_project_crud_and_overview_api(self):
        from projects.models import ProductLine, ProductVersion

        customer = Organization.objects.create(name="API 客户", org_type="customer")
        sales = Person.objects.create(name="API 销售", person_type="sales")
        line = ProductLine.objects.create(name="数据安全产线", code="DATA")
        product = Product.objects.create(name="数据库审计", product_code="DBA", product_line=line)
        version = ProductVersion.objects.create(product=product, version_name="V3.2", version_code="3.2")
        model = DeviceModel.objects.create(product=product, product_version=version, model_name="DA-2000", model_code="DA2000")
        device = Device.objects.create(name="审计设备", serial_number="API-SN-001", device_model=model)

        response = self.client.post("/api/projects/", {"project_no": "API-PRJ-001", "name": "API 项目", "customer_org": customer.id, "sales_person": sales.id}, format="json")
        self.assertEqual(response.status_code, 201)
        project_id = response.data["id"]

        bind_response = self.client.post("/api/project-devices/", {"project": project_id, "device": device.id, "quantity": 1}, format="json")
        self.assertEqual(bind_response.status_code, 201)

        overview = self.client.get(f"/api/projects/{project_id}/overview/")
        self.assertEqual(overview.status_code, 200)
        self.assertEqual(overview.data["project"]["name"], "API 项目")
        self.assertEqual(overview.data["customer"]["name"], "API 客户")
        self.assertEqual(overview.data["devices"][0]["serial_number"], "API-SN-001")


class ProjectDeviceDetailApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="project-device-detail", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_project_overview_returns_device_detail_fields(self):
        from projects.models import ProductLine, ProductVersion, Project, ProjectDevice

        line = ProductLine.objects.create(name="测试产线", code="TEST-LINE")
        product = Product.objects.create(name="测试产品", product_code="TEST-PRODUCT", product_line=line)
        version = ProductVersion.objects.create(product=product, version_name="V1.0", version_code="1.0")
        model = DeviceModel.objects.create(product=product, product_version=version, model_name="TEST-1000", model_code="TEST1000")
        device = Device.objects.create(
            name="测试设备",
            serial_number="DETAIL-SN-001",
            device_model=model,
            hardware_code="HW-001",
            software_version="OS-1.0",
            license_info={"type": "标准授权"},
            is_under_warranty=True,
            screenshot_url="https://example.com/device.png",
            rack_install_date="2026-07-01",
            management_address="https://10.0.0.1",
            version_update_method="远程升级",
            is_standard_product=True,
            supports_remote=True,
            remark="设备备注",
        )
        project = Project.objects.create(project_no="DETAIL-PRJ-001", name="设备详情项目")
        ops = Person.objects.create(name="现场运维", person_type="ops")
        device.ops_person = ops
        device.save(update_fields=["ops_person"])
        ProjectDevice.objects.create(project=project, device=device, device_project_type="正式设备")

        response = self.client.get(f"/api/projects/{project.id}/overview/")

        self.assertEqual(response.status_code, 200)
        detail = response.data["devices"][0]
        self.assertEqual(detail["hardware_code"], "HW-001")
        self.assertEqual(detail["software_version"], "OS-1.0")
        self.assertEqual(detail["license_info"], {"type": "标准授权"})
        self.assertTrue(detail["is_under_warranty"])
        self.assertEqual(detail["screenshot_url"], "https://example.com/device.png")
        self.assertEqual(detail["rack_install_date"], "2026-07-01")
        self.assertEqual(detail["management_address"], "https://10.0.0.1")
        self.assertEqual(detail["version_update_method"], "远程升级")
        self.assertTrue(detail["is_standard_product"])
        self.assertTrue(detail["supports_remote"])
        self.assertEqual(detail["device_project_type"], "正式设备")
        self.assertEqual(detail["ops_person"]["name"], "现场运维")
        self.assertEqual(detail["remark"], "设备备注")


class AttachmentUploadApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="attachment-api", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_upload_device_attachment_returns_preview_url(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from projects.models import ProductLine, ProductVersion

        line = ProductLine.objects.create(name="附件产线", code="ATTACH-LINE")
        product = Product.objects.create(name="附件产品", product_code="ATTACH-PRODUCT", product_line=line)
        version = ProductVersion.objects.create(product=product, version_name="V1", version_code="1")
        model = DeviceModel.objects.create(product=product, product_version=version, model_name="ATTACH-1000", model_code="ATTACH1000")
        device = Device.objects.create(name="附件设备", serial_number="ATTACH-SN-001", device_model=model)

        upload = SimpleUploadedFile("device.png", b"fake-image", content_type="image/png")
        response = self.client.post("/api/attachments/upload/", {"name": "设备截图", "object_type": "device", "object_id": device.id, "file": upload}, format="multipart")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["object_type"], "device")
        self.assertIn("file_url", response.data)
