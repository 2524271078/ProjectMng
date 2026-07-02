from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from accounts.models import Menu, Permission, Role, UserRole
from projects.models import Contract, ContractDevice, ContractParty, Device, DeviceModel, Organization, Person, Product, SalesCustomerRelation


class AccountApiTests(APITestCase):
    def test_login_returns_token_and_current_user_menus(self):
        user = User.objects.create_user(username="admin", password="pass123456")
        role = Role.objects.create(name="管理员", code="admin")
        menu = Menu.objects.create(name="客户中心", code="customers", path="/customers", order_index=1)
        Permission.objects.create(role=role, menu=menu, action="view")
        UserRole.objects.create(user=user, role=role)

        login = self.client.post("/api/auth/login/", {"username": "admin", "password": "pass123456"}, format="json")
        self.assertEqual(login.status_code, 200)
        self.assertIn("token", login.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")
        current = self.client.get("/api/auth/me/")

        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.data["username"], "admin")
        self.assertEqual(current.data["menus"][0]["code"], "customers")


class BusinessApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api", password="pass123456")
        self.client.force_authenticate(self.user)
        self.internal = Organization.objects.create(name="内部公司", org_type="internal_company")
        self.customer = Organization.objects.create(name="客户 A", org_type="customer")
        self.integrator = Organization.objects.create(name="集成商 A", org_type="integrator")
        self.vendor = Organization.objects.create(name="厂商 A", org_type="vendor")
        self.sales = Person.objects.create(name="销售 A", organization=self.internal, person_type="sales")
        self.ops = Person.objects.create(name="运维 A", organization=self.internal, person_type="ops")
        self.contact = Person.objects.create(name="联系人 A", organization=self.customer, person_type="customer_contact")
        SalesCustomerRelation.objects.create(sales_person=self.sales, customer_org=self.customer, relation_type="owner")
        self.product = Product.objects.create(name="产品 A", product_code="P-A", manufacturer=self.vendor)
        self.model = DeviceModel.objects.create(product=self.product, model_name="型号 A", model_code="M-A", manufacturer=self.vendor)
        self.device = Device.objects.create(name="设备 A", serial_number="SN-A", device_model=self.model, customer_org=self.customer, sales_person=self.sales, ops_person=self.ops)
        self.contract = Contract.objects.create(contract_no="C-A", contract_name="合同 A", final_customer=self.customer, direct_buyer=self.integrator, sales_person=self.sales, sign_date=date(2026, 1, 1), amount=Decimal("100.00"))
        ContractParty.objects.create(contract=self.contract, organization=self.customer, role="final_customer", order_index=1)
        ContractParty.objects.create(contract=self.contract, organization=self.integrator, role="direct_buyer", order_index=2)
        ContractDevice.objects.create(contract=self.contract, device=self.device, quantity=1, price=Decimal("80.00"))

    def test_crud_api_creates_organization(self):
        response = self.client.post("/api/organizations/", {"name": "新客户", "org_type": "customer"}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "新客户")

    def test_sales_customers_endpoint_returns_customer_devices_and_contracts(self):
        response = self.client.get(f"/api/sales/{self.sales.id}/customers/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "客户 A")
        self.assertEqual(response.data[0]["devices"][0]["serial_number"], "SN-A")
        self.assertEqual(response.data[0]["contracts"][0]["contract_no"], "C-A")



    def test_set_sales_customers_creates_relations_visible_in_customer_overview(self):
        customer = Organization.objects.create(name="客户 B", org_type="customer")
        response = self.client.post(f"/api/sales/{self.sales.id}/customer-relations/", {"customer_ids": [customer.id]}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["customer_ids"], [customer.id])
        overview = self.client.get(f"/api/customers/{customer.id}/overview/")
        self.assertEqual(overview.data["sales"][0]["name"], "销售 A")

    def test_customer_device_and_contract_overviews(self):
        customer = self.client.get(f"/api/customers/{self.customer.id}/overview/")
        device = self.client.get(f"/api/devices/{self.device.id}/overview/")
        contract = self.client.get(f"/api/contracts/{self.contract.id}/overview/")

        self.assertEqual(customer.status_code, 200)
        self.assertEqual(customer.data["contacts"][0]["name"], "联系人 A")
        self.assertEqual(device.status_code, 200)
        self.assertEqual(device.data["customer"]["name"], "客户 A")
        self.assertEqual(contract.status_code, 200)
        self.assertEqual(contract.data["parties"][0]["organization"]["name"], "客户 A")
