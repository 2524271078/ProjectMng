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
