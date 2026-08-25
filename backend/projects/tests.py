from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from projects.views import paginate_queryset, project_device_summary

from projects.models import (
    Attachment,
    AuditLog,
    Contract,
    ContractDevice,
    ContractParty,
    Device,
    DeviceModel,
    DeviceOperationRecord,
    DeviceServicePlan,
    DeviceServiceSchedule,
    InspectionTask,
    Organization,
    Person,
    Product,
    Project,
    ProjectContract,
    ProjectDevice,
    ProductLine,
    ProductVersion,
    SalesCustomerRelation,
    ServiceStandardTemplate,
)
from projects.serializers import DeviceOperationRecordSerializer, DeviceServicePlanSerializer, DeviceServiceScheduleSerializer
from projects.services import generate_inspection_tasks, generate_service_tasks, refresh_inspection_task_statuses


def api_results(response):
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


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


class CustomerPersonManagementApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="customer-person-api", password="pass123456")
        self.client.force_authenticate(self.user)
        self.customer = Organization.objects.create(name="客户人员维护客户", org_type="customer")

    def test_customer_center_can_create_and_delete_contact_synced_with_people(self):
        response = self.client.post(
            f"/api/organizations/{self.customer.id}/contacts/",
            {"name": "客户联系人甲", "position": "信息主管", "phone": "13800000001", "email": "contact@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        contact_id = response.data["id"]
        contact = Person.objects.get(pk=contact_id)
        self.assertEqual(contact.person_type, "customer_contact")
        self.assertEqual(contact.organization, self.customer)

        list_response = self.client.get(f"/api/organizations/{self.customer.id}/contacts/")
        self.assertEqual(api_results(list_response)[0]["id"], contact_id)

        delete_response = self.client.delete(f"/api/organizations/{self.customer.id}/contacts/{contact_id}/")
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Person.objects.filter(pk=contact_id).exists())
        self.assertTrue(Person.all_objects.get(pk=contact_id).is_deleted)

    def test_customer_center_can_create_and_remove_sales_relationship_without_deleting_person(self):
        response = self.client.post(
            f"/api/organizations/{self.customer.id}/sales/",
            {"name": "负责销售甲", "phone": "13800000002", "email": "sales@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        sales_id = response.data["id"]
        sales = Person.objects.get(pk=sales_id)
        self.assertEqual(sales.person_type, "sales")
        self.assertTrue(SalesCustomerRelation.objects.filter(sales_person=sales, customer_org=self.customer).exists())

        list_response = self.client.get(f"/api/organizations/{self.customer.id}/sales/")
        self.assertEqual(api_results(list_response)[0]["id"], sales_id)

        delete_response = self.client.delete(f"/api/organizations/{self.customer.id}/sales/{sales_id}/")
        self.assertEqual(delete_response.status_code, 204)
        self.assertTrue(Person.objects.filter(pk=sales_id).exists())
        self.assertFalse(SalesCustomerRelation.objects.filter(sales_person=sales, customer_org=self.customer).exists())
        self.assertTrue(SalesCustomerRelation.all_objects.get(sales_person=sales, customer_org=self.customer).is_deleted)

    def test_customer_center_can_link_existing_sales_and_reactivate_removed_relation(self):
        sales = Person.objects.create(name="已有销售", person_type="sales")
        SalesCustomerRelation.objects.create(sales_person=sales, customer_org=self.customer, relation_type="owner", is_deleted=True)

        response = self.client.post(
            f"/api/organizations/{self.customer.id}/sales/",
            {"sales_person": sales.id},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["id"], sales.id)
        relation = SalesCustomerRelation.objects.get(sales_person=sales, customer_org=self.customer, relation_type="owner")
        self.assertFalse(relation.is_deleted)


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
        names = [item["name"] for item in api_results(list_response)]
        self.assertNotIn("待删除客户", names)


class CustomerDeviceLatestProjectApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="customer-device-project", password="pass123456")
        self.client.force_authenticate(self.user)
        self.customer = Organization.objects.create(name="关联项目客户", org_type="customer")
        product = Product.objects.create(name="关联项目产品")
        model = DeviceModel.objects.create(product=product, model_name="关联项目设备名称")
        self.device = Device.objects.create(name="关联项目产品型号", serial_number="LATEST-PROJECT-SN", device_model=model, customer_org=self.customer)
        self.first_project = Project.objects.create(project_no="LATEST-001", name="初始交付项目", customer_org=self.customer)
        self.latest_project = Project.objects.create(project_no="LATEST-002", name="续保项目", customer_org=self.customer, signing_subject="agent")
        ProjectDevice.objects.create(
            project=self.first_project,
            device=self.device,
            service_type="new_install",
            service_start_date=date(2026, 1, 1),
            service_end_date=date(2026, 12, 31),
        )
        ProjectDevice.objects.create(
            project=self.latest_project,
            device=self.device,
            service_type="renewal",
            service_start_date=date(2027, 1, 1),
            service_end_date=date(2027, 12, 31),
        )

    def test_customer_device_list_returns_latest_service_project(self):
        response = self.client.get(f"/api/organizations/{self.customer.id}/devices/")

        self.assertEqual(response.status_code, 200)
        device = response.data["results"][0]
        self.assertEqual(device["latest_project"]["id"], self.latest_project.id)
        self.assertEqual(device["latest_project"]["name"], "续保项目")
        self.assertEqual(device["current_signing_subject"], "agent")

        filtered_response = self.client.get(f"/api/organizations/{self.customer.id}/devices/?signing_subject=agent")
        self.assertEqual(filtered_response.status_code, 200)
        self.assertEqual(filtered_response.data["count"], 1)

        device_center_response = self.client.get("/api/devices/?signing_subject=agent")
        self.assertEqual(device_center_response.status_code, 200)
        self.assertEqual(device_center_response.data["count"], 1)
        self.assertEqual(device_center_response.data["results"][0]["current_signing_subject"], "agent")

        search_by_serial = self.client.get(f"/api/organizations/{self.customer.id}/devices/?search=LATEST-PROJECT-SN")
        self.assertEqual(search_by_serial.status_code, 200)
        self.assertEqual(search_by_serial.data["count"], 1)

        search_by_device_name = self.client.get(f"/api/organizations/{self.customer.id}/devices/?search=关联项目设备名称")
        self.assertEqual(search_by_device_name.status_code, 200)
        self.assertEqual(search_by_device_name.data["count"], 1)



class PaginationHelperTests(TestCase):
    def test_paginate_queryset_applies_stable_pk_order_when_queryset_has_no_explicit_order(self):
        org = Organization.objects.create(name="Stable Org", org_type="internal_company")
        people = [
            Person.objects.create(name=f"Stable Person {index}", organization=org, person_type="sales")
            for index in range(3)
        ]
        request = SimpleNamespace(query_params={"page": "1", "page_size": "2"})

        page_items, meta = paginate_queryset(request, Person.objects.all())

        self.assertEqual(tuple(page_items.query.order_by), ("-created_at", "id"))
        self.assertEqual(
            list(page_items.values_list("id", flat=True)),
            list(Person.objects.order_by("-created_at", "id").values_list("id", flat=True)[:2]),
        )
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["total_pages"], 2)


class PaginationApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="pagination-api", password="pass123456")
        self.client.force_authenticate(self.user)
        self.org = Organization.objects.create(name="Pagination Org", org_type="internal_company")

    def test_people_list_returns_default_pagination_shape(self):
        for index in range(12):
            Person.objects.create(
                name=f"Sales Person {index:02d}",
                organization=self.org,
                person_type="sales",
            )

        response = self.client.get("/api/people/?person_type=sales")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"count", "page", "page_size", "total_pages", "results"},
        )
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 10)
        self.assertEqual(response.data["total_pages"], 2)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            list(Person.objects.filter(person_type="sales").order_by("-created_at", "id").values_list("id", flat=True)[:10]),
        )

    def test_organization_list_remains_unpaginated_for_tree_data(self):
        for index in range(3):
            Organization.objects.create(name=f"Customer {index}", org_type="customer")

        response = self.client.get("/api/organizations/")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 4)
        self.assertEqual([item["name"] for item in response.data], ["Pagination Org", "Customer 0", "Customer 1", "Customer 2"])

    def test_device_list_returns_pagination_envelope(self):
        product = Product.objects.create(name="Envelope Product", product_code="ENV-P")
        model = DeviceModel.objects.create(product=product, model_name="ENV-1000", model_code="ENV-1000")
        customer = Organization.objects.create(name="Envelope Customer", org_type="customer")
        Device.objects.create(name="Device A", serial_number="ENV-SN-001", device_model=model, customer_org=customer)

        response = self.client.get("/api/devices/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"count", "page", "page_size", "total_pages", "results"},
        )
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 10)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_people_list_supports_search_and_safe_invalid_pagination_params(self):
        Person.objects.create(name="Target Name", organization=self.org, person_type="sales")
        Person.objects.create(name="Other Name", organization=self.org, person_type="sales")
        Person.objects.create(name="Target Name", organization=self.org, person_type="customer_contact")

        response = self.client.get("/api/people/?person_type=sales&search=Target Name&page=abc&page_size=xyz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 10)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["total_pages"], 1)
        self.assertEqual([item["name"] for item in response.data["results"]], ["Target Name"])

    def test_people_list_clamps_non_positive_page_to_first_page(self):
        for index in range(3):
            Person.objects.create(name=f"Boundary Person {index}", organization=self.org, person_type="sales")

        zero_response = self.client.get("/api/people/?person_type=sales&page=0&page_size=2")
        negative_response = self.client.get("/api/people/?person_type=sales&page=-1&page_size=2")

        self.assertEqual(zero_response.status_code, 200)
        self.assertEqual(zero_response.data["page"], 1)
        self.assertEqual(zero_response.data["page_size"], 2)
        self.assertEqual(len(zero_response.data["results"]), 2)
        self.assertEqual(negative_response.status_code, 200)
        self.assertEqual(negative_response.data["page"], 1)
        self.assertEqual(negative_response.data["page_size"], 2)
        self.assertEqual(
            [item["id"] for item in negative_response.data["results"]],
            [item["id"] for item in zero_response.data["results"]],
        )

    def test_people_list_resets_non_positive_page_size_to_default(self):
        for index in range(12):
            Person.objects.create(name=f"Size Person {index}", organization=self.org, person_type="sales")

        zero_response = self.client.get("/api/people/?person_type=sales&page_size=0")
        negative_response = self.client.get("/api/people/?person_type=sales&page_size=-1")

        self.assertEqual(zero_response.status_code, 200)
        self.assertEqual(zero_response.data["page"], 1)
        self.assertEqual(zero_response.data["page_size"], 10)
        self.assertEqual(zero_response.data["total_pages"], 2)
        self.assertEqual(len(zero_response.data["results"]), 10)
        self.assertEqual(negative_response.status_code, 200)
        self.assertEqual(negative_response.data["page_size"], 10)
        self.assertEqual(negative_response.data["total_pages"], 2)
        self.assertEqual(len(negative_response.data["results"]), 10)



class SearchApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="search-api", password="pass123456")
        self.client.force_authenticate(self.user)
        self.internal_org = Organization.objects.create(name="盛邦安全", org_type="internal_company")
        self.vendor = Organization.objects.create(name="边界厂商", org_type="vendor")

    def test_organization_search_matches_name_region_and_org_type(self):
        Organization.objects.create(name="华东能源集团", org_type="customer", region="华北")
        Organization.objects.create(name="西南客户", org_type="customer", region="华东大区")
        Organization.objects.create(name="渠道伙伴", org_type="华东渠道", region="华南")
        Organization.objects.create(name="华南客户", org_type="customer", region="华南")

        response = self.client.get("/api/organizations/?search=华东")

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in api_results(response)]
        self.assertCountEqual(names, ["华东能源集团", "西南客户", "渠道伙伴"])

    def test_person_search_can_stack_with_sales_person_type_filter(self):
        sales_org = Organization.objects.create(name="内部销售组织", org_type="internal_company")
        customer = Organization.objects.create(name="目标客户", org_type="customer")
        Person.objects.create(name="许超", organization=sales_org, person_type="sales")
        Person.objects.create(name="许超", organization=customer, person_type="customer_contact")
        Person.objects.create(name="李四", organization=sales_org, person_type="sales")

        response = self.client.get("/api/people/?person_type=sales&search=许超")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in api_results(response)], ["许超"])
        self.assertTrue(all(item["person_type"] == "sales" for item in api_results(response)))


    def test_product_list_hides_orphan_and_deleted_line_products(self):
        active_line = ProductLine.objects.create(name="有效产线", code="ACTIVE-LINE")
        deleted_line = ProductLine.objects.create(name="已删产线", code="DELETED-LINE", is_deleted=True)
        active_product = Product.objects.create(name="有效产品", product_code="ACTIVE-PRODUCT", product_line=active_line, manufacturer=self.vendor)
        Product.objects.create(name="孤儿产品", product_code="ORPHAN-PRODUCT", manufacturer=self.vendor)
        Product.objects.create(name="残留产品", product_code="DELETED-LINE-PRODUCT", product_line=deleted_line, manufacturer=self.vendor)

        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in api_results(response)]
        self.assertIn(active_product.name, names)
        self.assertNotIn("孤儿产品", names)
        self.assertNotIn("残留产品", names)

    def test_project_search_matches_customer_organization_name(self):
        customer = Organization.objects.create(name="国网华北电力", org_type="customer")
        Project.objects.create(project_no="PRJ-SEARCH-001", name="区域加固项目", customer_org=customer)
        Project.objects.create(project_no="PRJ-SEARCH-002", name="普通项目")

        response = self.client.get("/api/projects/?search=国网")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["project_no"] for item in api_results(response)], ["PRJ-SEARCH-001"])

    def test_project_search_matches_sales_person_name(self):
        sales = Person.objects.create(name="许超飞", organization=self.internal_org, person_type="sales")
        other_sales = Person.objects.create(name="李四", organization=self.internal_org, person_type="sales")
        Project.objects.create(project_no="PRJ-SEARCH-003", name="销售归属项目", sales_person=sales)
        Project.objects.create(project_no="PRJ-SEARCH-004", name="其他销售项目", sales_person=other_sales)

        response = self.client.get("/api/projects/?search=许超飞")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["project_no"] for item in api_results(response)], ["PRJ-SEARCH-003"])

    def test_project_search_matches_project_stage(self):
        Project.objects.create(project_no="PRJ-SEARCH-005", name="交付阶段项目", project_stage="delivery")
        Project.objects.create(project_no="PRJ-SEARCH-006", name="售前阶段项目", project_stage="presale")

        response = self.client.get("/api/projects/?search=delivery")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["project_no"] for item in api_results(response)], ["PRJ-SEARCH-005"])

    def test_project_list_supports_combined_name_customer_sales_and_signing_subject_filters(self):
        customer = Organization.objects.create(name="Target Customer", org_type="customer")
        sales = Person.objects.create(name="Target Sales", organization=self.internal_org, person_type="sales")
        target = Project.objects.create(
            project_no="PROJECT-FILTER-001",
            name="Target Project",
            customer_org=customer,
            sales_person=sales,
            signing_subject="agent",
        )
        Project.objects.create(
            project_no="PROJECT-FILTER-002",
            name="Other Project",
            customer_org=customer,
            sales_person=sales,
            signing_subject="direct",
        )

        response = self.client.get(
            "/api/projects/?project_name=Target%20Project&customer_name=Target%20Customer&sales_name=Target%20Sales&signing_subject=agent"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in api_results(response)], [target.id])

    def test_device_model_search_matches_model_code(self):
        product = Product.objects.create(name="边界防护平台", product_code="EDGE-P", manufacturer=self.vendor)
        DeviceModel.objects.create(product=product, model_name="边界一体机 3000", model_code="SG3000", manufacturer=self.vendor)
        DeviceModel.objects.create(product=product, model_name="边界一体机 5000", model_code="SG5000", manufacturer=self.vendor)

        response = self.client.get("/api/device-models/?search=SG3000")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["model_code"] for item in api_results(response)], ["SG3000"])

    def test_device_model_search_matches_product_name(self):
        target_product = Product.objects.create(name="边界防护平台", product_code="EDGE-P2", manufacturer=self.vendor)
        other_product = Product.objects.create(name="数据库审计平台", product_code="DBA-P", manufacturer=self.vendor)
        DeviceModel.objects.create(product=target_product, model_name="边界防护一体机", model_code="DM-EDGE-1", manufacturer=self.vendor)
        DeviceModel.objects.create(product=other_product, model_name="数据库审计一体机", model_code="DM-DBA-1", manufacturer=self.vendor)

        response = self.client.get("/api/device-models/?search=边界防护")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["model_code"] for item in api_results(response)], ["DM-EDGE-1"])

    def test_device_model_search_can_stack_with_product_version_scope(self):
        line = ProductLine.objects.create(name="边界安全产品线", code="EDGE-LINE")
        target_product = Product.objects.create(name="边界防护平台", product_code="EDGE-P3", product_line=line, manufacturer=self.vendor)
        other_product = Product.objects.create(name="边界防护平台副线", product_code="EDGE-P4", product_line=line, manufacturer=self.vendor)
        target_version = ProductVersion.objects.create(product=target_product, version_name="专用版", version_code="VER-TARGET")
        other_version = ProductVersion.objects.create(product=other_product, version_name="通用版", version_code="VER-OTHER")
        DeviceModel.objects.create(
            product=target_product,
            product_version=target_version,
            model_name="边界防护专用型号",
            model_code="EDGE-TARGET",
            manufacturer=self.vendor,
        )
        DeviceModel.objects.create(
            product=other_product,
            product_version=other_version,
            model_name="边界防护通用型号",
            model_code="EDGE-OTHER",
            manufacturer=self.vendor,
        )

        response = self.client.get(f"/api/device-models/?product_version={target_version.id}&search=边界防护")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["model_code"] for item in api_results(response)], ["EDGE-TARGET"])

    def test_device_model_scope_filters_work_without_search(self):
        line_a = ProductLine.objects.create(name="边界安全产品线", code="EDGE-LINE-A")
        line_b = ProductLine.objects.create(name="数据安全产品线", code="DATA-LINE-B")
        product_a = Product.objects.create(name="边界防护平台 A", product_code="EDGE-SCOPE-A", product_line=line_a, manufacturer=self.vendor)
        product_b = Product.objects.create(name="数据库审计平台 B", product_code="DATA-SCOPE-B", product_line=line_b, manufacturer=self.vendor)
        version_a = ProductVersion.objects.create(product=product_a, version_name="V1", version_code="SCOPE-V1")
        version_b = ProductVersion.objects.create(product=product_b, version_name="V2", version_code="SCOPE-V2")
        DeviceModel.objects.create(product=product_a, product_version=version_a, model_name="范围过滤型号 A", model_code="SCOPE-A", manufacturer=self.vendor)
        DeviceModel.objects.create(product=product_b, product_version=version_b, model_name="范围过滤型号 B", model_code="SCOPE-B", manufacturer=self.vendor)

        by_line = self.client.get(f"/api/device-models/?product_line={line_a.id}")
        by_product = self.client.get(f"/api/device-models/?product={product_a.id}")
        by_version = self.client.get(f"/api/device-models/?product_version={version_a.id}")

        self.assertEqual(by_line.status_code, 200)
        self.assertEqual([item["model_code"] for item in api_results(by_line)], ["SCOPE-A"])
        self.assertEqual([item["model_code"] for item in api_results(by_product)], ["SCOPE-A"])
        self.assertEqual([item["model_code"] for item in api_results(by_version)], ["SCOPE-A"])

    def test_device_model_scope_prefers_product_version_over_product_and_product_line(self):
        line_primary = ProductLine.objects.create(name="优先级产品线", code="PRIORITY-LINE-1")
        line_secondary = ProductLine.objects.create(name="次级产品线", code="PRIORITY-LINE-2")
        product_primary = Product.objects.create(name="优先级产品", product_code="PRIORITY-PRODUCT-1", product_line=line_primary, manufacturer=self.vendor)
        product_secondary = Product.objects.create(name="次级产品", product_code="PRIORITY-PRODUCT-2", product_line=line_secondary, manufacturer=self.vendor)
        version_primary = ProductVersion.objects.create(product=product_primary, version_name="主版本", version_code="PRIORITY-V1")
        version_secondary = ProductVersion.objects.create(product=product_secondary, version_name="副版本", version_code="PRIORITY-V2")
        DeviceModel.objects.create(product=product_primary, product_version=version_primary, model_name="优先级型号 A", model_code="PRIORITY-A", manufacturer=self.vendor)
        DeviceModel.objects.create(product=product_secondary, product_version=version_secondary, model_name="优先级型号 B", model_code="PRIORITY-B", manufacturer=self.vendor)

        response = self.client.get(
            f"/api/device-models/?product_line={line_primary.id}&product={product_primary.id}&product_version={version_secondary.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["model_code"] for item in api_results(response)], ["PRIORITY-B"])

    def test_device_model_scope_ignores_invalid_value_without_500(self):
        line = ProductLine.objects.create(name="非法值产品线", code="INVALID-LINE")
        product = Product.objects.create(name="非法值产品", product_code="INVALID-PRODUCT", product_line=line, manufacturer=self.vendor)
        version = ProductVersion.objects.create(product=product, version_name="非法值版本", version_code="INVALID-V1")
        DeviceModel.objects.create(product=product, product_version=version, model_name="非法值型号 A", model_code="INVALID-A", manufacturer=self.vendor)
        DeviceModel.objects.create(product=product, model_name="非法值型号 B", model_code="INVALID-B", manufacturer=self.vendor)

        response = self.client.get("/api/device-models/?product_version=abc")

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual([item["model_code"] for item in api_results(response)], ["INVALID-A", "INVALID-B"])

    def test_device_model_scope_skips_invalid_more_specific_value_and_uses_next_valid_scope(self):
        line_a = ProductLine.objects.create(name="回退产品线 A", code="FALLBACK-LINE-A")
        line_b = ProductLine.objects.create(name="回退产品线 B", code="FALLBACK-LINE-B")
        product_a = Product.objects.create(name="回退产品 A", product_code="FALLBACK-PRODUCT-A", product_line=line_a, manufacturer=self.vendor)
        product_b = Product.objects.create(name="回退产品 B", product_code="FALLBACK-PRODUCT-B", product_line=line_b, manufacturer=self.vendor)
        DeviceModel.objects.create(product=product_a, model_name="回退型号 A", model_code="FALLBACK-A", manufacturer=self.vendor)
        DeviceModel.objects.create(product=product_b, model_name="回退型号 B", model_code="FALLBACK-B", manufacturer=self.vendor)

        response = self.client.get(f"/api/device-models/?product_version=abc&product={product_a.id}&product_line={line_b.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["model_code"] for item in api_results(response)], ["FALLBACK-A"])


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


class ProductCatalogOptionalCodeTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="catalog-optional-code", password="pass123456")
        self.client.force_authenticate(self.user)
        self.vendor = Organization.objects.create(name="Catalog Vendor", org_type="vendor")
        self.line = ProductLine.objects.create(name="Catalog Line", code="CAT-LINE")
        self.product = Product.objects.create(name="Catalog Product", product_code="CAT-PRODUCT", product_line=self.line, manufacturer=self.vendor)

    def test_product_can_be_created_without_product_code(self):
        response = self.client.post(
            "/api/products/",
            {
                "product_line": self.line.id,
                "name": "Product Without Code",
                "product_code": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["product_code"], "")

    def test_product_version_can_be_created_without_version_code(self):
        response = self.client.post(
            "/api/product-versions/",
            {
                "product": self.product.id,
                "version_name": "Version Without Code",
                "version_code": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["version_code"], "")

    def test_device_model_can_be_created_without_model_code(self):
        response = self.client.post(
            "/api/device-models/",
            {
                "product": self.product.id,
                "model_name": "Model Without Code",
                "model_code": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["model_code"], "")

    def test_device_model_still_rejects_duplicate_nonempty_model_code(self):
        DeviceModel.objects.create(product=self.product, model_name="Existing Model", model_code="DUPLICATE-CODE")

        response = self.client.post(
            "/api/device-models/",
            {
                "product": self.product.id,
                "model_name": "Another Model",
                "model_code": "DUPLICATE-CODE",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("model_code", response.data)


class ProjectApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="project-api", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_project_api_generates_number_when_project_number_is_blank(self):
        response = self.client.post("/api/projects/", {"project_no": "", "name": "自动编号项目"}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertRegex(response.data["project_no"], r"^PRJ-\d{8}-0001$")

    def test_project_api_keeps_manually_entered_project_number(self):
        response = self.client.post("/api/projects/", {"project_no": "CUSTOM-PRJ-001", "name": "手工编号项目"}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["project_no"], "CUSTOM-PRJ-001")

    def test_project_api_saves_signing_subject(self):
        response = self.client.post(
            "/api/projects/",
            {"project_no": "SIGNING-SUBJECT-001", "name": "代理签约项目", "signing_subject": "agent"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["signing_subject"], "agent")

    def test_project_crud_and_overview_api(self):
        from projects.models import ProductLine, ProductVersion

        customer = Organization.objects.create(name="API 客户", org_type="customer")
        sales = Person.objects.create(name="API 销售", person_type="sales")
        contact = Person.objects.create(name="API 客户联系人", organization=customer, person_type="customer_contact", position="项目经理")
        line = ProductLine.objects.create(name="数据安全产线", code="DATA")
        product = Product.objects.create(name="数据库审计", product_code="DBA", product_line=line)
        version = ProductVersion.objects.create(product=product, version_name="V3.2", version_code="3.2")
        model = DeviceModel.objects.create(product=product, product_version=version, model_name="DA-2000", model_code="DA2000")
        device = Device.objects.create(name="审计设备", serial_number="API-SN-001", device_model=model)

        response = self.client.post("/api/projects/", {"project_no": "API-PRJ-001", "name": "API 项目", "customer_org": customer.id, "customer_contact": contact.id, "sales_person": sales.id, "winning_company": "中标公司 A", "contact_company": "对接公司 B"}, format="json")
        self.assertEqual(response.status_code, 201)
        project_id = response.data["id"]

        list_response = self.client.get("/api/projects/")
        self.assertEqual(list_response.status_code, 200)
        project_row = next(item for item in api_results(list_response) if item["id"] == project_id)
        self.assertEqual(project_row["customer_org_detail"]["name"], "API 客户")
        self.assertEqual(project_row["sales_person_detail"]["name"], "API 销售")

        bind_response = self.client.post("/api/project-devices/", {"project": project_id, "device": device.id, "quantity": 1}, format="json")
        self.assertEqual(bind_response.status_code, 201)

        overview = self.client.get(f"/api/projects/{project_id}/overview/")
        self.assertEqual(overview.status_code, 200)
        self.assertEqual(overview.data["project"]["name"], "API 项目")
        self.assertEqual(overview.data["project"]["winning_company"], "中标公司 A")
        self.assertEqual(overview.data["project"]["contact_company"], "对接公司 B")
        self.assertEqual(overview.data["customer"]["name"], "API 客户")
        self.assertEqual(overview.data["customer_contact"]["name"], "API 客户联系人")
        self.assertEqual(overview.data["customer_contact"]["position"], "项目经理")
        self.assertEqual(overview.data["devices"][0]["serial_number"], "API-SN-001")
        self.assertEqual(overview.data["devices"][0]["device_model_detail"]["model_name"], "DA-2000")
        self.assertEqual(overview.data["devices"][0]["device_model_detail"]["model_code"], "DA2000")


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
        ProjectDevice.objects.create(project=project, device=device, device_project_type="正式设备", service_type="new_install", service_start_date="2026-07-01", service_end_date="2027-06-30")

        response = self.client.get(f"/api/projects/{project.id}/overview/")

        self.assertEqual(response.status_code, 200)
        detail = response.data["devices"][0]
        self.assertEqual(detail["device_id"], device.id)
        self.assertEqual(detail["hardware_code"], "HW-001")
        self.assertEqual(detail["software_version"], "OS-1.0")
        self.assertEqual(detail["license_info"], {"type": "标准授权"})
        self.assertTrue(detail["is_under_warranty"])
        self.assertEqual(detail["service_status"], "保内")
        self.assertEqual(detail["service_end_date"], "2027-06-30")
        self.assertEqual(detail["screenshot_url"], "https://example.com/device.png")
        self.assertEqual(detail["rack_install_date"], "2026-07-01")
        self.assertEqual(detail["management_address"], "https://10.0.0.1")
        self.assertEqual(detail["version_update_method"], "远程升级")
        self.assertTrue(detail["is_standard_product"])
        self.assertTrue(detail["supports_remote"])
        self.assertEqual(detail["device_project_type"], "正式设备")
        self.assertEqual(detail["ops_person"]["name"], "现场运维")
        self.assertEqual(detail["remark"], "设备备注")
        self.assertEqual(detail["device_model_detail"]["model_name"], "TEST-1000")
        self.assertEqual(detail["device_model_detail"]["model_code"], "TEST1000")
        self.assertEqual(detail["device_model_detail"]["product_name"], "测试产品")
        self.assertEqual(detail["device_model_detail"]["product_version_name"], "V1.0")


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


    def test_upload_project_contract_attachment_is_visible_in_project_overview(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from projects.models import Project

        project = Project.objects.create(project_no="ATTACH-PRJ-001", name="附件项目")
        upload = SimpleUploadedFile("contract.pdf", b"fake-pdf", content_type="application/pdf")
        response = self.client.post("/api/attachments/upload/", {"name": "合同附件", "object_type": "project", "object_id": project.id, "file": upload}, format="multipart")
        self.assertEqual(response.status_code, 201)

        overview = self.client.get(f"/api/projects/{project.id}/overview/")
        self.assertEqual(overview.status_code, 200)
        self.assertEqual(overview.data["attachments"][0]["name"], "合同附件")
        self.assertIn("file_url", overview.data["attachments"][0])


class ProjectContractModelTests(TestCase):
    def test_project_contract_active_relation_is_unique(self):
        customer = Organization.objects.create(name="唯一性客户", org_type="customer")
        project = Project.objects.create(project_no="UNIQ-PRJ-001", name="唯一性项目", customer_org=customer)
        contract = Contract.objects.create(contract_no="UNIQ-CON-001", contract_name="唯一性合同", final_customer=customer)

        ProjectContract.objects.create(project=project, contract=contract)

        with self.assertRaises(Exception):
            ProjectContract.objects.create(project=project, contract=contract)


class CustomerDetailPaginationTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="customer-detail-pagination", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_customer_detail_paginated_endpoints_return_envelope_and_filter_by_customer(self):
        customer = Organization.objects.create(name="Paged Customer", org_type="customer")
        other_customer = Organization.objects.create(name="Other Customer", org_type="customer")
        internal = Organization.objects.create(name="Internal Sales Org", org_type="internal_company")

        primary_contact = Person.objects.create(name="Primary Contact", organization=customer, person_type="customer_contact")
        Person.objects.create(name="Secondary Contact", organization=customer, person_type="customer_contact")
        Person.objects.create(name="Other Contact", organization=other_customer, person_type="customer_contact")

        sales = Person.objects.create(name="Owner Sales", organization=internal, person_type="sales")
        other_sales = Person.objects.create(name="Other Sales", organization=internal, person_type="sales")
        SalesCustomerRelation.objects.create(sales_person=sales, customer_org=customer, relation_type="owner")
        SalesCustomerRelation.objects.create(sales_person=other_sales, customer_org=other_customer, relation_type="owner")

        product = Product.objects.create(name="Customer Page Product", product_code="CUST-PAGE-P")
        model = DeviceModel.objects.create(product=product, model_name="CUST-PAGE-1000", model_code="CUST-PAGE-1000")
        paged_project = Project.objects.create(
            project_no="CUST-PROJ-001",
            name="Customer Project 1",
            customer_org=customer,
            customer_contact=primary_contact,
            sales_person=sales,
        )
        Project.objects.create(project_no="CUST-PROJ-999", name="Other Project", customer_org=other_customer, sales_person=other_sales)
        for index in range(12):
            device = Device.objects.create(
                name=f"Customer Device {index}",
                serial_number=f"CUST-DEVICE-{index:02d}",
                device_model=model,
                customer_org=customer if index < 2 else None,
                sales_person=sales,
            )
            ProjectDevice.objects.create(project=paged_project, device=device, service_type="renewal")

        other_device = Device.objects.create(name="Other Device", serial_number="OTHER-DEVICE-01", device_model=model, customer_org=other_customer)
        other_project = Project.objects.get(project_no="CUST-PROJ-999")
        ProjectDevice.objects.create(project=other_project, device=other_device, service_type="renewal")

        target_contract = Contract.objects.create(contract_no="CUST-CON-001", contract_name="Customer Contract", final_customer=customer, sales_person=sales)
        Contract.objects.create(contract_no="CUST-CON-999", contract_name="Other Contract", final_customer=other_customer, sales_person=other_sales)
        ProjectContract.objects.create(project=paged_project, contract=target_contract)

        device_response = self.client.get(f"/api/organizations/{customer.id}/devices/?page=2&page_size=10")
        project_response = self.client.get(f"/api/organizations/{customer.id}/projects/")
        contract_response = self.client.get(f"/api/organizations/{customer.id}/contracts/")
        contact_response = self.client.get(f"/api/organizations/{customer.id}/contacts/")
        sales_response = self.client.get(f"/api/organizations/{customer.id}/sales/")

        for response in [device_response, project_response, contract_response, contact_response, sales_response]:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(set(response.data.keys()), {"count", "page", "page_size", "total_pages", "results"})

        self.assertEqual(device_response.data["count"], 12)
        self.assertEqual(device_response.data["page"], 2)
        self.assertEqual(device_response.data["page_size"], 10)
        self.assertEqual(device_response.data["total_pages"], 2)
        self.assertEqual(len(device_response.data["results"]), 2)
        self.assertTrue(all(item["serial_number"].startswith("CUST-DEVICE-") for item in device_response.data["results"]))

        self.assertEqual(project_response.data["count"], 1)
        self.assertEqual([item["project_no"] for item in project_response.data["results"]], ["CUST-PROJ-001"])

        self.assertEqual(contract_response.data["count"], 1)
        self.assertEqual([item["contract_no"] for item in contract_response.data["results"]], ["CUST-CON-001"])

        self.assertEqual(contact_response.data["count"], 2)
        self.assertCountEqual([item["name"] for item in contact_response.data["results"]], ["Primary Contact", "Secondary Contact"])

        self.assertEqual(sales_response.data["count"], 1)
        self.assertEqual([item["name"] for item in sales_response.data["results"]], ["Owner Sales"])


class ProjectDetailPaginationTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="project-detail-pagination", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_project_detail_paginated_endpoints_return_envelope_and_filter_by_project(self):
        customer = Organization.objects.create(name="Project Page Customer", org_type="customer")
        other_customer = Organization.objects.create(name="Other Project Customer", org_type="customer")
        project = Project.objects.create(project_no="PAGE-PRJ-002", name="Paged Project", customer_org=customer)
        other_project = Project.objects.create(project_no="PAGE-PRJ-999", name="Other Project", customer_org=other_customer)
        product = Product.objects.create(name="Project Page Product", product_code="PAGE-PROJECT-P")
        model = DeviceModel.objects.create(product=product, model_name="PAGE-2000", model_code="PAGE-2000")

        for index in range(11):
            device = Device.objects.create(name=f"Project Device {index}", serial_number=f"PRJ-DEVICE-{index:02d}", device_model=model)
            ProjectDevice.objects.create(project=project, device=device, service_type="new_install")
        other_device = Device.objects.create(name="Other Project Device", serial_number="OTHER-PRJ-DEVICE", device_model=model)
        ProjectDevice.objects.create(project=other_project, device=other_device, service_type="renewal")

        contract = Contract.objects.create(contract_no="PRJ-CON-001", contract_name="Project Contract", final_customer=customer)
        other_contract = Contract.objects.create(contract_no="PRJ-CON-999", contract_name="Other Project Contract", final_customer=other_customer)
        ProjectContract.objects.create(project=project, contract=contract)
        ProjectContract.objects.create(project=other_project, contract=other_contract)

        Attachment.objects.create(name="Project Attachment", object_type="project", object_id=project.id)
        Attachment.objects.create(name="Other Attachment", object_type="project", object_id=other_project.id)

        device_response = self.client.get(f"/api/projects/{project.id}/devices/?page=2&page_size=10")
        contract_response = self.client.get(f"/api/projects/{project.id}/contracts/")
        attachment_response = self.client.get(f"/api/projects/{project.id}/attachments/")

        for response in [device_response, contract_response, attachment_response]:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(set(response.data.keys()), {"count", "page", "page_size", "total_pages", "results"})

        self.assertEqual(device_response.data["count"], 11)
        self.assertEqual(device_response.data["page"], 2)
        self.assertEqual(device_response.data["page_size"], 10)
        self.assertEqual(device_response.data["total_pages"], 2)
        self.assertEqual(len(device_response.data["results"]), 1)
        self.assertEqual(device_response.data["results"][0]["project"], project.id)

        self.assertEqual(contract_response.data["count"], 1)
        self.assertEqual([item["contract_no"] for item in contract_response.data["results"]], ["PRJ-CON-001"])

        self.assertEqual(attachment_response.data["count"], 1)
        self.assertEqual([item["name"] for item in attachment_response.data["results"]], ["Project Attachment"])


class CustomerProjectOverviewTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="customer-projects", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_customer_overview_includes_projects(self):
        customer = Organization.objects.create(name="客户项目客户", org_type="customer")
        contact = Person.objects.create(name="客户联系人", organization=customer, person_type="customer_contact")
        sales = Person.objects.create(name="客户销售", person_type="sales")
        project = Project.objects.create(
            project_no="CUST-PRJ-001",
            name="客户归属项目",
            customer_org=customer,
            customer_contact=contact,
            sales_person=sales,
            amount=Decimal("123.00"),
        )

        response = self.client.get(f"/api/customers/{customer.id}/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["projects"][0]["id"], project.id)
        self.assertEqual(response.data["projects"][0]["project_no"], "CUST-PRJ-001")
        self.assertEqual(response.data["projects"][0]["customer_contact"]["id"], contact.id)
        self.assertEqual(response.data["projects"][0]["sales_person"]["id"], sales.id)


class CustomerPurchasedDeviceTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="customer-devices", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_customer_overview_includes_project_linked_devices(self):
        customer = Organization.objects.create(name="设备客户", org_type="customer")
        product = Product.objects.create(name="客户设备产品", product_code="CUST-DEV")
        model = DeviceModel.objects.create(product=product, model_name="CUST-1000", model_code="CUST-1000")
        device = Device.objects.create(name="项目挂接设备", serial_number="CUST-SN-001", device_model=model)
        project = Project.objects.create(project_no="CUST-DEV-001", name="客户设备项目", customer_org=customer)
        ProjectDevice.objects.create(project=project, device=device, service_type="renewal", service_start_date="2026-01-01", service_end_date="2026-12-31")

        response = self.client.get(f"/api/customers/{customer.id}/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["devices"]), 1)
        self.assertEqual(response.data["devices"][0]["serial_number"], "CUST-SN-001")


class ProjectContractOverviewTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="project-contracts", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_project_overview_includes_related_contracts(self):
        customer = Organization.objects.create(name="项目合同客户", org_type="customer")
        project = Project.objects.create(project_no="PRJ-CON-001", name="项目合同测试", customer_org=customer)
        contract = Contract.objects.create(
            contract_no="CON-001",
            contract_name="项目关联合同",
            final_customer=customer,
            amount=Decimal("88.00"),
        )
        ProjectContract.objects.create(project=project, contract=contract)

        response = self.client.get(f"/api/projects/{project.id}/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["contracts"][0]["contract_no"], "CON-001")


class ProjectDeviceServiceCycleTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="service-cycle", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_project_device_stores_service_cycle_fields(self):
        customer = Organization.objects.create(name="服务周期客户", org_type="customer")
        project = Project.objects.create(project_no="SVC-PRJ-001", name="服务周期项目", customer_org=customer)
        product = Product.objects.create(name="服务周期产品", product_code="SVC-P")
        model = DeviceModel.objects.create(product=product, model_name="SVC-1000", model_code="SVC-1000")
        device = Device.objects.create(name="服务周期设备", serial_number="SVC-SN-001", device_model=model, customer_org=customer)

        response = self.client.post("/api/project-devices/", {
            "project": project.id,
            "device": device.id,
            "service_type": "renewal",
            "service_start_date": "2026-07-01",
            "service_end_date": "2027-06-30",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["service_type"], "renewal")
        self.assertEqual(response.data["service_end_date"], "2027-06-30")


class ProjectDeviceOfflineStateTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="project-device-offline", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_project_device_stores_offline_type_and_offline_date(self):
        customer = Organization.objects.create(name="Offline Customer", org_type="customer")
        project = Project.objects.create(project_no="OFFLINE-PRJ-001", name="Offline Project", customer_org=customer)
        product = Product.objects.create(name="Offline Product", product_code="OFFLINE-P")
        model = DeviceModel.objects.create(product=product, model_name="OFFLINE-1000", model_code="OFFLINE-1000")
        device = Device.objects.create(name="Offline Device", serial_number="OFFLINE-SN-001", device_model=model, customer_org=customer)

        response = self.client.post("/api/project-devices/", {
            "project": project.id,
            "device": device.id,
            "service_type": "offline",
            "service_start_date": "2026-07-01",
            "service_end_date": "2027-06-30",
            "offline_date": "2026-12-31",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["service_type"], "offline")
        self.assertEqual(response.data["offline_date"], "2026-12-31")

    def test_project_overview_device_summary_includes_offline_date(self):
        customer = Organization.objects.create(name="Offline Overview Customer", org_type="customer")
        project = Project.objects.create(project_no="OFFLINE-PRJ-002", name="Offline Overview Project", customer_org=customer)
        product = Product.objects.create(name="Offline Overview Product", product_code="OFFLINE-OV-P")
        model = DeviceModel.objects.create(product=product, model_name="OFFLINE-OV-1000", model_code="OFFLINE-OV-1000")
        device = Device.objects.create(name="Offline Overview Device", serial_number="OFFLINE-OV-SN-001", device_model=model, customer_org=customer)
        ProjectDevice.objects.create(
            project=project,
            device=device,
            service_type="offline",
            service_start_date="2026-07-01",
            service_end_date="2027-06-30",
            offline_date="2026-12-31",
        )

        response = self.client.get(f"/api/projects/{project.id}/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["devices"][0]["service_type"], "offline")
        self.assertEqual(response.data["devices"][0]["offline_date"], "2026-12-31")


class DeviceCurrentServiceStatusTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="device-service-status", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_device_overview_uses_latest_project_service_cycle(self):
        customer = Organization.objects.create(name="状态客户", org_type="customer")
        project_old = Project.objects.create(project_no="OLD-001", name="旧项目", customer_org=customer)
        project_new = Project.objects.create(project_no="NEW-001", name="新项目", customer_org=customer)
        product = Product.objects.create(name="状态产品", product_code="STATUS-P")
        model = DeviceModel.objects.create(product=product, model_name="STATUS-1000", model_code="STATUS-1000")
        device = Device.objects.create(name="状态设备", serial_number="STATUS-SN-001", device_model=model, customer_org=customer)

        ProjectDevice.objects.create(project=project_old, device=device, service_type="new_install", service_start_date="2025-01-01", service_end_date="2025-12-31")
        ProjectDevice.objects.create(project=project_new, device=device, service_type="renewal", service_start_date="2026-01-01", service_end_date="2027-12-31", deploy_location="A区机房", offline_date="2027-01-15")

        response = self.client.get(f"/api/devices/{device.id}/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["device"]["current_service_status"], "保内")
        self.assertEqual(response.data["device"]["current_service_end_date"], "2027-12-31")
        self.assertEqual(response.data["device"]["service_type"], "renewal")
        self.assertEqual(response.data["device"]["deploy_location"], "A区机房")
        self.assertEqual(response.data["device"]["offline_date"], "2027-01-15")
        latest_binding = next(item for item in response.data["project_devices"] if item["project"] == project_new.id)
        self.assertEqual(latest_binding["deploy_location"], "A区机房")
        self.assertEqual(latest_binding["service_type"], "renewal")
        self.assertEqual(latest_binding["service_start_date"], "2026-01-01")



class DeviceDirectoryApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="device-directory", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_device_list_excludes_devices_only_bound_to_deleted_project_and_customer(self):
        deleted_customer = Organization.objects.create(name="已删客户", org_type="customer", is_deleted=True)
        product = Product.objects.create(name="残留设备产品", product_code="DEVICE-DELETED-P")
        model = DeviceModel.objects.create(product=product, model_name="DEVICE-DELETED-1000", model_code="DEVICE-DELETED-1000")
        device = Device.objects.create(name="残留设备", serial_number="DEVICE-DELETED-SN-001", device_model=model)
        deleted_project = Project.objects.create(project_no="DEVICE-DELETED-PRJ-001", name="已删项目", customer_org=deleted_customer, is_deleted=True)
        ProjectDevice.objects.create(project=deleted_project, device=device, service_type="renewal", service_start_date="2026-07-01", service_end_date="2027-06-30")

        response = self.client.get("/api/devices/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(device.id, [item["id"] for item in api_results(response)])

    def test_device_list_includes_customer_contact_customer_org_and_sales_details(self):
        customer = Organization.objects.create(name="设备中心客户", org_type="customer")
        contact = Person.objects.create(name="设备中心联系人", organization=customer, person_type="customer_contact", position="信息主管")
        sales = Person.objects.create(name="设备中心销售", person_type="sales")
        product = Product.objects.create(name="设备中心产品", product_code="DEVICE-DIR-P")
        model = DeviceModel.objects.create(product=product, model_name="DEVICE-DIR-1000", model_code="DEVICE-DIR-1000")
        device = Device.objects.create(
            name="设备中心设备",
            serial_number="DEVICE-DIR-SN-001",
            device_model=model,
            customer_org=customer,
            sales_person=sales,
        )
        project = Project.objects.create(
            project_no="DEVICE-DIR-PRJ-001",
            name="设备中心项目",
            customer_org=customer,
            customer_contact=contact,
            sales_person=sales,
        )
        ProjectDevice.objects.create(
            project=project,
            device=device,
            service_type="renewal",
            service_start_date="2026-07-01",
            service_end_date="2027-06-30",
        )

        response = self.client.get("/api/devices/")

        self.assertEqual(response.status_code, 200)
        item = next(row for row in api_results(response) if row["id"] == device.id)
        self.assertEqual(item["customer_org_detail"]["id"], customer.id)
        self.assertEqual(item["customer_org_detail"]["name"], "设备中心客户")
        self.assertEqual(item["customer_contact_detail"]["id"], contact.id)
        self.assertEqual(item["customer_contact_detail"]["name"], "设备中心联系人")
        self.assertEqual(item["sales_person_detail"]["id"], sales.id)
        self.assertEqual(item["sales_person_detail"]["name"], "设备中心销售")
        self.assertEqual(item["current_service_start_date"], "2026-07-01")
        self.assertEqual(item["current_service_end_date"], "2027-06-30")
        self.assertEqual(item["device_model_detail"]["model_name"], "DEVICE-DIR-1000")
        self.assertEqual(item["device_model_detail"]["model_code"], "DEVICE-DIR-1000")

    def test_device_overview_includes_customer_contact_detail(self):
        customer = Organization.objects.create(name="设备详情客户", org_type="customer")
        contact = Person.objects.create(name="设备详情联系人", organization=customer, person_type="customer_contact")
        sales = Person.objects.create(name="设备详情销售", person_type="sales")
        product = Product.objects.create(name="设备详情产品", product_code="DEVICE-OVERVIEW-P")
        model = DeviceModel.objects.create(product=product, model_name="DEVICE-OVERVIEW-1000", model_code="DEVICE-OVERVIEW-1000")
        device = Device.objects.create(
            name="设备详情设备",
            serial_number="DEVICE-OVERVIEW-SN-001",
            device_model=model,
            customer_org=customer,
            sales_person=sales,
        )
        project = Project.objects.create(
            project_no="DEVICE-OVERVIEW-PRJ-001",
            name="设备详情项目",
            customer_org=customer,
            customer_contact=contact,
            sales_person=sales,
        )
        ProjectDevice.objects.create(
            project=project,
            device=device,
            service_type="new_install",
            service_start_date="2026-07-01",
            service_end_date="2027-06-30",
        )

        response = self.client.get(f"/api/devices/{device.id}/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["customer"]["id"], customer.id)
        self.assertEqual(response.data["customer_contact"]["id"], contact.id)
        self.assertEqual(response.data["customer_contact"]["name"], "设备详情联系人")
        self.assertEqual(response.data["sales_person"]["id"], sales.id)
        self.assertEqual(response.data["device"]["device_model_detail"]["model_name"], "DEVICE-OVERVIEW-1000")
        self.assertEqual(response.data["device"]["device_model_detail"]["model_code"], "DEVICE-OVERVIEW-1000")



class DeviceDirectorySearchApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="device-directory-search", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_device_list_search_matches_device_customer_contact_and_sales(self):
        customer = Organization.objects.create(name="搜索客户", org_type="customer")
        contact = Person.objects.create(name="搜索联系人", organization=customer, person_type="customer_contact")
        sales = Person.objects.create(name="搜索销售", person_type="sales")
        product = Product.objects.create(name="搜索产品", product_code="DEVICE-SEARCH-P")
        model = DeviceModel.objects.create(product=product, model_name="SEARCH-1000", model_code="SEARCH-1000")
        device = Device.objects.create(
            name="搜索设备",
            serial_number="SEARCH-SN-001",
            device_model=model,
            customer_org=customer,
            sales_person=sales,
        )
        project = Project.objects.create(
            project_no="DEVICE-SEARCH-PRJ-001",
            name="搜索项目",
            customer_org=customer,
            customer_contact=contact,
            sales_person=sales,
        )
        ProjectDevice.objects.create(
            project=project,
            device=device,
            service_type="new_install",
            service_start_date="2026-07-01",
            service_end_date="2027-06-30",
        )

        other_customer = Organization.objects.create(name="无关客户", org_type="customer")
        other_contact = Person.objects.create(name="无关联系人", organization=other_customer, person_type="customer_contact")
        other_sales = Person.objects.create(name="无关销售", person_type="sales")
        other_product = Product.objects.create(name="无关产品", product_code="DEVICE-SEARCH-OTHER-P")
        other_model = DeviceModel.objects.create(product=other_product, model_name="OTHER-1000", model_code="OTHER-1000")
        other_device = Device.objects.create(
            name="无关设备",
            serial_number="OTHER-SN-001",
            device_model=other_model,
            customer_org=other_customer,
            sales_person=other_sales,
        )
        other_project = Project.objects.create(
            project_no="DEVICE-SEARCH-PRJ-002",
            name="无关项目",
            customer_org=other_customer,
            customer_contact=other_contact,
            sales_person=other_sales,
        )
        ProjectDevice.objects.create(
            project=other_project,
            device=other_device,
            service_type="renewal",
            service_start_date="2026-08-01",
            service_end_date="2027-07-31",
        )

        by_device = self.client.get("/api/devices/?search=搜索设备")
        by_serial = self.client.get("/api/devices/?search=SEARCH-SN-001")
        by_customer = self.client.get("/api/devices/?search=搜索客户")
        by_contact = self.client.get("/api/devices/?search=搜索联系人")
        by_sales = self.client.get("/api/devices/?search=搜索销售")

        for response in [by_device, by_serial, by_customer, by_contact, by_sales]:
            self.assertEqual(response.status_code, 200)
            self.assertEqual([item["id"] for item in api_results(response)], [device.id])

    def test_device_list_search_matches_project_sales_when_device_sales_is_empty(self):
        customer = Organization.objects.create(name="项目销售客户", org_type="customer")
        contact = Person.objects.create(name="项目销售联系人", organization=customer, person_type="customer_contact")
        sales = Person.objects.create(name="许超飞", person_type="sales")
        product = Product.objects.create(name="项目销售产品", product_code="DEVICE-PROJECT-SALES-P")
        model = DeviceModel.objects.create(product=product, model_name="PROJECT-SALES-1000", model_code="PROJECT-SALES-1000")
        device = Device.objects.create(
            name="项目继承销售设备",
            serial_number="PROJECT-SALES-SN-001",
            device_model=model,
            customer_org=customer,
            sales_person=None,
        )
        project = Project.objects.create(
            project_no="DEVICE-PROJECT-SALES-PRJ-001",
            name="项目继承销售项目",
            customer_org=customer,
            customer_contact=contact,
            sales_person=sales,
        )
        ProjectDevice.objects.create(
            project=project,
            device=device,
            service_type="renewal",
            service_start_date="2026-07-01",
            service_end_date="2027-06-30",
        )

        response = self.client.get("/api/devices/?search=许超飞")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in api_results(response)], [device.id])

    def test_device_list_supports_combined_device_customer_and_sales_filters(self):
        customer = Organization.objects.create(name="Target Customer", org_type="customer")
        sales = Person.objects.create(name="Target Sales", person_type="sales")
        product = Product.objects.create(name="Target Product", product_code="TARGET-FILTER-P")
        model = DeviceModel.objects.create(product=product, model_name="Target Device", model_code="TARGET-FILTER-M")
        target = Device.objects.create(
            name="Target Asset",
            serial_number="TARGET-FILTER-SN",
            device_model=model,
            customer_org=customer,
            sales_person=sales,
            software_version="V2.5.1",
        )
        other_customer = Organization.objects.create(name="Other Customer", org_type="customer")
        other_sales = Person.objects.create(name="Other Sales", person_type="sales")
        other_product = Product.objects.create(name="Other Product", product_code="OTHER-FILTER-P")
        other_model = DeviceModel.objects.create(product=other_product, model_name="Other Device", model_code="OTHER-FILTER-M")
        Device.objects.create(
            name="Other Asset",
            serial_number="OTHER-FILTER-SN",
            device_model=other_model,
            customer_org=other_customer,
            sales_person=other_sales,
            software_version="V3.0.0",
        )

        response = self.client.get(
            "/api/devices/?device_name=Target%20Device&customer_name=Target%20Customer&sales_name=Target%20Sales&software_version=V2.5"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in api_results(response)], [target.id])


class DataScopeFilteringTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from accounts.models import UserAccessProfile, UserSalesScope

        self.user = User.objects.create_user(username="scope-user", password="pass123456")
        self.client.force_authenticate(self.user)
        self.internal = Organization.objects.create(name="权限内部组织", org_type="internal_company")
        self.allowed_sales = Person.objects.create(name="允许销售", organization=self.internal, person_type="sales")
        self.other_sales = Person.objects.create(name="其他销售", organization=self.internal, person_type="sales")
        profile = UserAccessProfile.objects.create(user=self.user, data_scope_type=UserAccessProfile.DATA_SCOPE_CUSTOM)
        UserSalesScope.objects.create(profile=profile, sales_person=self.allowed_sales)

        self.allowed_customer = Organization.objects.create(name="允许客户", org_type="customer")
        self.other_customer = Organization.objects.create(name="其他客户", org_type="customer")
        SalesCustomerRelation.objects.create(sales_person=self.allowed_sales, customer_org=self.allowed_customer, relation_type="owner")
        SalesCustomerRelation.objects.create(sales_person=self.other_sales, customer_org=self.other_customer, relation_type="owner")

        product = Product.objects.create(name="权限产品", product_code="SCOPE-P")
        model = DeviceModel.objects.create(product=product, model_name="SCOPE-1000", model_code="SCOPE-1000")

        self.allowed_project = Project.objects.create(project_no="SCOPE-PRJ-1", name="允许项目", customer_org=self.allowed_customer, sales_person=self.allowed_sales)
        self.other_project = Project.objects.create(project_no="SCOPE-PRJ-2", name="其他项目", customer_org=self.other_customer, sales_person=self.other_sales)

        self.allowed_device = Device.objects.create(name="允许设备", serial_number="SCOPE-DEVICE-1", device_model=model, customer_org=self.allowed_customer, sales_person=self.allowed_sales)
        self.fallback_device = Device.objects.create(name="回退设备", serial_number="SCOPE-DEVICE-2", device_model=model, customer_org=self.allowed_customer, sales_person=None)
        self.other_device = Device.objects.create(name="其他设备", serial_number="SCOPE-DEVICE-3", device_model=model, customer_org=self.other_customer, sales_person=self.other_sales)
        ProjectDevice.objects.create(project=self.allowed_project, device=self.allowed_device, service_type="new_install")
        ProjectDevice.objects.create(project=self.allowed_project, device=self.fallback_device, service_type="renewal")
        ProjectDevice.objects.create(project=self.other_project, device=self.other_device, service_type="renewal")

        self.allowed_contract = Contract.objects.create(contract_no="SCOPE-CON-1", contract_name="允许合同", final_customer=self.allowed_customer, sales_person=self.allowed_sales)
        self.other_contract = Contract.objects.create(contract_no="SCOPE-CON-2", contract_name="其他合同", final_customer=self.other_customer, sales_person=self.other_sales)

    def test_project_list_is_filtered_by_authorized_sales(self):
        response = self.client.get('/api/projects/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in api_results(response)], [self.allowed_project.id])

    def test_device_list_allows_direct_and_project_fallback_sales_matches(self):
        response = self.client.get('/api/devices/')

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            [item['id'] for item in api_results(response)],
            [self.allowed_device.id, self.fallback_device.id],
        )

    def test_customer_customer_tree_query_only_returns_authorized_customers(self):
        response = self.client.get('/api/organizations/?org_type=customer')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [self.allowed_customer.id])

    def test_sales_people_list_and_overview_are_filtered(self):
        sales_response = self.client.get('/api/people/?person_type=sales')
        visible_sales_ids = [item['id'] for item in api_results(sales_response)]
        self.assertEqual(visible_sales_ids, [self.allowed_sales.id])

        allowed_customers = self.client.get(f'/api/sales/{self.allowed_sales.id}/customers/')
        blocked_customers = self.client.get(f'/api/sales/{self.other_sales.id}/customers/')
        self.assertEqual(allowed_customers.status_code, 200)
        self.assertEqual(len(allowed_customers.data), 1)
        self.assertEqual(blocked_customers.status_code, 200)
        self.assertEqual(blocked_customers.data, [])

    def test_customer_project_contract_and_overview_block_unauthorized_records(self):
        allowed_customer = self.client.get(f'/api/customers/{self.allowed_customer.id}/overview/')
        blocked_customer = self.client.get(f'/api/customers/{self.other_customer.id}/overview/')
        allowed_project = self.client.get(f'/api/projects/{self.allowed_project.id}/overview/')
        blocked_project = self.client.get(f'/api/projects/{self.other_project.id}/overview/')
        allowed_contract = self.client.get(f'/api/contracts/{self.allowed_contract.id}/overview/')
        blocked_contract = self.client.get(f'/api/contracts/{self.other_contract.id}/overview/')

        self.assertEqual(allowed_customer.status_code, 200)
        self.assertEqual(blocked_customer.status_code, 404)
        self.assertEqual(allowed_project.status_code, 200)
        self.assertEqual(blocked_project.status_code, 404)
        self.assertEqual(allowed_contract.status_code, 200)
        self.assertEqual(blocked_contract.status_code, 404)


class DeviceServicePlanTests(TestCase):
    def setUp(self):
        customer = Organization.objects.create(name="服务客户", org_type="customer")
        product = Product.objects.create(name="服务产品")
        model = DeviceModel.objects.create(product=product, model_name="服务设备名称")
        device = Device.objects.create(name="服务产品型号", serial_number="SERVICE-SN-001", device_model=model)
        project = Project.objects.create(project_no="SERVICE-PROJECT-001", name="服务项目", customer_org=customer)
        self.project_device = ProjectDevice.objects.create(
            project=project,
            device=device,
            service_start_date=date(2026, 1, 1),
            service_end_date=date(2026, 12, 31),
        )

    def test_plan_copies_selected_template_as_effective_snapshot(self):
        template = ServiceStandardTemplate.objects.create(
            name="季度巡检标准",
            code="QUARTERLY-INSPECTION",
            inspection_frequency=ServiceStandardTemplate.INSPECTION_QUARTERLY,
            reminder_days=10,
            service_contents=["inspection", "system_upgrade"],
        )

        serializer = DeviceServicePlanSerializer(data={
            "project_device": self.project_device.id,
            "template": template.id,
            "first_inspection_date": "2026-08-01",
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        plan = serializer.save()
        self.assertEqual(plan.inspection_frequency, ServiceStandardTemplate.INSPECTION_QUARTERLY)
        self.assertEqual(plan.reminder_days, 10)
        self.assertEqual(plan.standard_snapshot["template_name"], "季度巡检标准")
        self.assertEqual(plan.standard_snapshot["service_contents"], ["inspection", "system_upgrade"])

    def test_system_upgrade_content_creates_upgrade_schedule_and_tasks(self):
        serializer = DeviceServicePlanSerializer(data={
            "project_device": self.project_device.id,
            "inspection_frequency": ServiceStandardTemplate.INSPECTION_SEMIANNUAL,
            "first_inspection_date": "2026-02-01",
            "service_contents": ["system_upgrade"],
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        plan = serializer.save()
        schedule = plan.service_schedules.get(service_type=DeviceServiceSchedule.TYPE_SYSTEM_UPGRADE)
        self.assertEqual(schedule.tasks.count(), 2)
        self.assertTrue(schedule.tasks.filter(task_type=DeviceServiceSchedule.TYPE_SYSTEM_UPGRADE).exists())

    def test_custom_frequency_requires_interval_days(self):
        serializer = DeviceServicePlanSerializer(data={
            "project_device": self.project_device.id,
            "inspection_frequency": ServiceStandardTemplate.INSPECTION_CUSTOM,
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("inspection_interval_days", serializer.errors)

    def test_project_device_allows_only_one_active_service_plan(self):
        DeviceServicePlan.objects.create(project_device=self.project_device)
        serializer = DeviceServicePlanSerializer(data={
            "project_device": self.project_device.id,
            "inspection_frequency": ServiceStandardTemplate.INSPECTION_QUARTERLY,
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("project_device", serializer.errors)

    def test_quarterly_plan_generates_tasks_and_marks_overdue(self):
        plan = DeviceServicePlan.objects.create(
            project_device=self.project_device,
            inspection_frequency=ServiceStandardTemplate.INSPECTION_QUARTERLY,
            first_inspection_date=date(2026, 1, 15),
            reminder_days=7,
            service_contents=["inspection"],
        )
        schedule = DeviceServiceSchedule.objects.create(
            service_plan=plan,
            service_type=DeviceServiceSchedule.TYPE_INSPECTION,
            frequency=plan.inspection_frequency,
            first_service_date=plan.first_inspection_date,
            reminder_days=plan.reminder_days,
        )

        self.assertEqual(generate_service_tasks(schedule), 4)
        tasks = plan.inspection_tasks.order_by("planned_date")
        self.assertEqual([task.planned_date for task in tasks], [date(2026, 1, 15), date(2026, 4, 15), date(2026, 7, 15), date(2026, 10, 15)])
        reminders = refresh_inspection_task_statuses(date(2026, 1, 16))
        self.assertEqual(InspectionTask.objects.get(pk=tasks.first().id).status, InspectionTask.STATUS_OVERDUE)
        self.assertEqual(reminders.count(), 1)

    def test_upgrade_schedule_generates_upgrade_tasks_and_upgrade_record_completes_task(self):
        plan = DeviceServicePlan.objects.create(project_device=self.project_device)
        schedule = DeviceServiceSchedule.objects.create(
            service_plan=plan,
            service_type=DeviceServiceSchedule.TYPE_SYSTEM_UPGRADE,
            frequency=ServiceStandardTemplate.INSPECTION_SEMIANNUAL,
            first_service_date=date(2026, 2, 1),
        )

        self.assertEqual(generate_service_tasks(schedule), 2)
        task = schedule.tasks.order_by("planned_date").first()
        serializer = DeviceOperationRecordSerializer(data={
            "device": self.project_device.device_id,
            "project_device": self.project_device.id,
            "service_plan": plan.id,
            "inspection_task": task.id,
            "record_type": DeviceOperationRecord.TYPE_SYSTEM_UPGRADE,
            "performed_at": datetime(2026, 2, 1, 9, 0).isoformat(),
            "software_version_after": "V3.0",
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        task.refresh_from_db()
        self.assertEqual(task.task_type, DeviceServiceSchedule.TYPE_SYSTEM_UPGRADE)
        self.assertEqual(task.status, InspectionTask.STATUS_COMPLETED)

    def test_inspection_record_completes_task_and_updates_versions(self):
        plan = DeviceServicePlan.objects.create(project_device=self.project_device, service_contents=["inspection"])
        task = InspectionTask.objects.create(service_plan=plan, planned_date=date(2026, 7, 30))
        serializer = DeviceOperationRecordSerializer(data={
            "device": self.project_device.device_id,
            "project_device": self.project_device.id,
            "service_plan": plan.id,
            "inspection_task": task.id,
            "record_type": DeviceOperationRecord.TYPE_INSPECTION,
            "performed_at": datetime(2026, 7, 30, 9, 0).isoformat(),
            "software_version_after": "V2.0",
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        task.refresh_from_db()
        self.project_device.device.refresh_from_db()
        self.assertEqual(task.status, InspectionTask.STATUS_COMPLETED)
        self.assertEqual(self.project_device.device.software_version, "V2.0")

    def test_project_device_summary_includes_next_inspection_overview(self):
        plan = DeviceServicePlan.objects.create(
            project_device=self.project_device,
            inspection_frequency=ServiceStandardTemplate.INSPECTION_QUARTERLY,
            service_contents=["inspection"],
        )
        task = InspectionTask.objects.create(service_plan=plan, planned_date=date(2026, 8, 1))

        summary = project_device_summary(self.project_device)

        self.assertEqual(summary["service_overview"]["plan_id"], plan.id)
        self.assertEqual(summary["service_overview"]["next_inspection_task"]["id"], task.id)

    def test_edit_service_plan_syncs_service_items(self):
        plan = DeviceServicePlan.objects.create(
            project_device=self.project_device,
            service_contents=["inspection"],
        )
        inspection_schedule = DeviceServiceSchedule.objects.create(
            service_plan=plan,
            service_type=DeviceServiceSchedule.TYPE_INSPECTION,
            frequency=ServiceStandardTemplate.INSPECTION_QUARTERLY,
        )
        generate_service_tasks(inspection_schedule)

        serializer = DeviceServicePlanSerializer(
            plan,
            data={"service_contents": ["system_upgrade"]},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        inspection_schedule.refresh_from_db()
        self.assertTrue(inspection_schedule.is_deleted)
        upgrade_schedule = DeviceServiceSchedule.objects.get(service_plan=plan, service_type=DeviceServiceSchedule.TYPE_SYSTEM_UPGRADE)
        self.assertTrue(upgrade_schedule.tasks.exists())

    def test_edit_service_plan_syncs_pending_task_assignees(self):
        original_assignee = Person.objects.create(name="原负责人", person_type="ops")
        new_assignee = Person.objects.create(name="新负责人", person_type="ops")
        plan = DeviceServicePlan.objects.create(project_device=self.project_device, ops_person=original_assignee)
        pending_task = InspectionTask.objects.create(service_plan=plan, planned_date=date(2026, 8, 1), assignee=original_assignee)
        completed_task = InspectionTask.objects.create(
            service_plan=plan,
            planned_date=date(2026, 8, 2),
            assignee=original_assignee,
            status=InspectionTask.STATUS_COMPLETED,
        )

        serializer = DeviceServicePlanSerializer(plan, data={"ops_person": new_assignee.id}, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        pending_task.refresh_from_db()
        completed_task.refresh_from_db()
        self.assertEqual(pending_task.assignee, new_assignee)
        self.assertEqual(completed_task.assignee, original_assignee)

    def test_edit_service_schedule_regenerates_pending_tasks(self):
        plan = DeviceServicePlan.objects.create(project_device=self.project_device)
        schedule = DeviceServiceSchedule.objects.create(
            service_plan=plan,
            service_type=DeviceServiceSchedule.TYPE_INSPECTION,
            frequency=ServiceStandardTemplate.INSPECTION_QUARTERLY,
            first_service_date=date(2026, 1, 1),
        )
        generate_service_tasks(schedule)
        old_task_ids = list(schedule.tasks.values_list("id", flat=True))

        serializer = DeviceServiceScheduleSerializer(
            schedule,
            data={"frequency": ServiceStandardTemplate.INSPECTION_SEMIANNUAL},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assertEqual(InspectionTask.objects.filter(id__in=old_task_ids).count(), 0)
        self.assertEqual(schedule.tasks.count(), 2)

    def test_edit_service_schedule_syncs_pending_task_assignee(self):
        assignee = Person.objects.create(name="服务项负责人", person_type="ops")
        plan = DeviceServicePlan.objects.create(project_device=self.project_device)
        schedule = DeviceServiceSchedule.objects.create(
            service_plan=plan,
            service_type=DeviceServiceSchedule.TYPE_INSPECTION,
            frequency=ServiceStandardTemplate.INSPECTION_QUARTERLY,
        )
        pending_task = InspectionTask.objects.create(service_plan=plan, service_schedule=schedule, planned_date=date(2026, 8, 1))
        completed_task = InspectionTask.objects.create(
            service_plan=plan,
            service_schedule=schedule,
            planned_date=date(2026, 8, 2),
            status=InspectionTask.STATUS_COMPLETED,
        )

        serializer = DeviceServiceScheduleSerializer(schedule, data={"assignee": assignee.id}, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        pending_task.refresh_from_db()
        completed_task.refresh_from_db()
        self.assertEqual(pending_task.assignee, assignee)
        self.assertIsNone(completed_task.assignee)


class DashboardReminderApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="reminder-user", password="pass123456")
        self.client.force_authenticate(self.user)
        self.ops_person = Person.objects.create(name="提醒负责人", person_type="ops", user=self.user)
        today = timezone.localdate()
        customer = Organization.objects.create(name="提醒客户", org_type="customer")
        self.sales = Person.objects.create(name="提醒销售", person_type="sales")
        product = Product.objects.create(name="提醒产品", product_code="REMINDER-P")
        model = DeviceModel.objects.create(product=product, model_name="提醒设备", model_code="REMINDER-M")
        device = Device.objects.create(name="提醒资产", serial_number="REMINDER-SN", device_model=model, customer_org=customer, sales_person=self.sales)
        project = Project.objects.create(project_no="REMINDER-PRJ", name="提醒项目", customer_org=customer, sales_person=self.sales)
        self.project_device = ProjectDevice.objects.create(
            project=project,
            device=device,
            service_start_date=today - timedelta(days=30),
            service_end_date=today + timedelta(days=60),
        )
        plan = DeviceServicePlan.objects.create(project_device=self.project_device, ops_person=self.ops_person)
        self.task = InspectionTask.objects.create(
            service_plan=plan,
            planned_date=today + timedelta(days=3),
            reminder_date=today,
            assignee=self.ops_person,
        )

    def test_dashboard_lists_expiring_service_and_due_service_task_and_hides_confirmed_item(self):
        response = self.client.get("/api/dashboard-reminders/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        keys = {item["key"] for item in response.data["results"]}
        expiry_key = f"service-expiring:{self.project_device.id}:{self.project_device.service_end_date.isoformat()}"
        self.assertIn(expiry_key, keys)
        self.assertIn(f"service-task:{self.task.id}", keys)
        task_reminder = next(item for item in response.data["results"] if item["key"] == f"service-task:{self.task.id}")
        self.assertIn("客户：提醒客户", task_reminder["content"])
        self.assertIn("设备：提醒设备（REMINDER-SN）", task_reminder["content"])

        confirmed = self.client.post("/api/dashboard-reminders/confirm/", {"reminder_key": expiry_key}, format="json")
        self.assertEqual(confirmed.status_code, 204)

        response = self.client.get("/api/dashboard-reminders/")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["key"], f"service-task:{self.task.id}")

    def test_dashboard_uses_the_same_sales_scope_as_device_center(self):
        from accounts.models import UserAccessProfile, UserSalesScope

        other_sales = Person.objects.create(name="其他销售", person_type="sales")
        customer = Organization.objects.create(name="无权限客户", org_type="customer")
        product = Product.objects.create(name="无权限产品", product_code="OUT-OF-SCOPE-P")
        model = DeviceModel.objects.create(product=product, model_name="无权限设备", model_code="OUT-OF-SCOPE-M")
        device = Device.objects.create(name="无权限资产", serial_number="OUT-OF-SCOPE-SN", device_model=model, customer_org=customer, sales_person=other_sales)
        project = Project.objects.create(project_no="OUT-OF-SCOPE-PRJ", name="无权限项目", customer_org=customer, sales_person=other_sales)
        out_of_scope_binding = ProjectDevice.objects.create(
            project=project,
            device=device,
            service_start_date=timezone.localdate(),
            service_end_date=timezone.localdate() + timedelta(days=60),
        )
        DeviceServicePlan.objects.create(project_device=out_of_scope_binding, ops_person=self.ops_person)
        profile = UserAccessProfile.objects.create(user=self.user, data_scope_type=UserAccessProfile.DATA_SCOPE_CUSTOM)
        UserSalesScope.objects.create(profile=profile, sales_person=self.sales)

        response = self.client.get("/api/dashboard-reminders/")

        keys = {item["key"] for item in response.data["results"]}
        self.assertIn(f"service-expiring:{self.project_device.id}:{self.project_device.service_end_date.isoformat()}", keys)
        self.assertNotIn(f"service-expiring:{out_of_scope_binding.id}:{out_of_scope_binding.service_end_date.isoformat()}", keys)

    def test_dashboard_only_shows_service_reminders_to_the_assigned_person(self):
        from django.contrib.auth.models import User

        other_user = User.objects.create_user(username="other-ops-user", password="pass123456")
        Person.objects.create(name="其他负责人", person_type="ops", user=other_user)
        self.client.force_authenticate(other_user)

        response = self.client.get("/api/dashboard-reminders/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_dashboard_superuser_sees_all_service_reminders(self):
        from django.contrib.auth.models import User

        superuser = User.objects.create_superuser(username="dashboard-superuser", password="pass123456", email="root@example.com")
        self.client.force_authenticate(superuser)

        response = self.client.get("/api/dashboard-reminders/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)


class DashboardOverviewApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.client.force_authenticate(User.objects.create_superuser(
            username="overview-superuser",
            password="pass123456",
            email="overview@example.com",
        ))
        self.today = timezone.localdate()
        self.customer_a = Organization.objects.create(name="总览客户甲", org_type="customer")
        self.customer_b = Organization.objects.create(name="总览客户乙", org_type="customer")
        self.product = Product.objects.create(name="总览产品", product_code="OVERVIEW-P")
        self.model = DeviceModel.objects.create(product=self.product, model_name="总览型号", model_code="OVERVIEW-M")

    def create_device(self, suffix, customer, start_date=None, end_date=None):
        device = Device.objects.create(
            name=f"总览设备{suffix}",
            serial_number=f"OVERVIEW-SN-{suffix}",
            device_model=self.model,
            customer_org=customer,
        )
        if start_date or end_date:
            project = Project.objects.create(
                project_no=f"OVERVIEW-PRJ-{suffix}",
                name=f"总览项目{suffix}",
                customer_org=customer,
            )
            ProjectDevice.objects.create(
                project=project,
                device=device,
                service_start_date=start_date,
                service_end_date=end_date,
            )
        return device

    def test_dashboard_overview_groups_current_device_service_statuses_and_customers(self):
        self.create_device("long", self.customer_a, self.today - timedelta(days=1), self.today + timedelta(days=200))
        self.create_device("near", self.customer_a, self.today - timedelta(days=1), self.today + timedelta(days=15))
        self.create_device("later", self.customer_b, self.today - timedelta(days=1), self.today + timedelta(days=100))
        self.create_device("expired", self.customer_b, self.today - timedelta(days=90), self.today - timedelta(days=1))
        self.create_device("unmaintained", self.customer_a)

        response = self.client.get("/api/dashboard-overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["metrics"], {
            "devices_total": 5,
            "in_warranty": 3,
            "expiring_30": 1,
            "expired": 1,
            "customers_total": 2,
        })
        status_counts = {item["key"]: item["count"] for item in response.data["service_status"]}
        self.assertEqual(status_counts, {
            "in_warranty": 1,
            "expiring_30": 1,
            "expiring_180": 1,
            "expired": 1,
            "unmaintained": 1,
        })
        self.assertEqual(sum(item["count"] for item in response.data["expiry_trend"]), 2)
        self.assertEqual({item["customer_name"] for item in response.data["attention_customers"]}, {"总览客户甲", "总览客户乙"})
