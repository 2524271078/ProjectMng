from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from accounts.models import Menu, Permission, Role, UserAccessProfile, UserRole, UserSalesScope
from projects.models import Contract, ContractDevice, ContractParty, Device, DeviceModel, Organization, Person, Product, SalesCustomerRelation


class AccountApiTests(APITestCase):
    def test_role_permissions_block_unauthorized_mutations(self):
        user = User.objects.create_user(username="limited-user", password="pass123456")
        role = Role.objects.create(name="只读客户", code="customer-reader")
        menu = Menu.objects.create(name="客户中心", code="customers", path="/customers", order_index=1)
        Permission.objects.create(role=role, menu=menu, action="view")
        UserRole.objects.create(user=user, role=role)
        self.client.force_authenticate(user)

        denied = self.client.post("/api/organizations/", {"name": "无权新增", "org_type": "customer"}, format="json")

        self.assertEqual(denied.status_code, 403)
        Permission.objects.create(role=role, menu=menu, action="create")
        allowed = self.client.post("/api/organizations/", {"name": "允许新增", "org_type": "customer"}, format="json")
        self.assertEqual(allowed.status_code, 201)

    def test_unsupported_device_center_actions_do_not_grant_device_mutation_access(self):
        user = User.objects.create_user(username="device-reader", password="pass123456")
        role = Role.objects.create(name="设备查看", code="device-reader")
        menu = Menu.objects.create(name="设备中心", code="device-center", path="/device-center", order_index=1)
        Permission.objects.create(role=role, menu=menu, action="view")
        # Existing roles may still contain this historical record. It must not
        # enable a write because the device-center menu is view-only.
        Permission.objects.create(role=role, menu=menu, action="create")
        UserRole.objects.create(user=user, role=role)
        self.client.force_authenticate(user)

        response = self.client.post("/api/devices/", {}, format="json")

        self.assertEqual(response.status_code, 403)

    def test_login_returns_token_and_current_user_permissions_and_scope(self):
        user = User.objects.create_user(username="admin", password="pass123456")
        role = Role.objects.create(name="管理员", code="admin")
        menu = Menu.objects.create(name="客户中心", code="customers", path="/customers", order_index=1)
        Permission.objects.create(role=role, menu=menu, action="view")
        UserRole.objects.create(user=user, role=role)
        sales = Person.objects.create(name="许超飞", person_type="sales")
        other_sales = Person.objects.create(name="P1", person_type="sales")
        sales.user = user
        sales.save(update_fields=["user"])
        profile = UserAccessProfile.objects.create(user=user, data_scope_type=UserAccessProfile.DATA_SCOPE_CUSTOM)
        UserSalesScope.objects.create(profile=profile, sales_person=sales)
        UserSalesScope.objects.create(profile=profile, sales_person=other_sales)

        login = self.client.post("/api/auth/login/", {"username": "admin", "password": "pass123456"}, format="json")
        self.assertEqual(login.status_code, 200)
        self.assertIn("token", login.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")
        current = self.client.get("/api/auth/me/")

        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.data["username"], "admin")
        self.assertEqual(current.data["menus"][0]["code"], "customers")
        self.assertEqual(current.data["permissions"][0], ["customers", "view"])
        self.assertEqual(current.data["access_profile"]["data_scope_type"], UserAccessProfile.DATA_SCOPE_CUSTOM)
        self.assertEqual(current.data["access_profile"]["bound_person"]["id"], sales.id)
        self.assertEqual(len(current.data["access_profile"]["sales_scope"]), 2)

    def test_role_api_auto_generates_code_when_missing(self):
        operator = User.objects.create_superuser(username="root", password="pass123456", email="root@example.com")
        self.client.force_authenticate(operator)

        response = self.client.post("/api/roles/", {
            "name": "项目经理",
            "remark": "自动编码",
            "status": "active",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["code"].startswith("role-"))

    def test_menu_api_bootstraps_default_menus_when_empty(self):
        operator = User.objects.create_superuser(username="root2", password="pass123456", email="root2@example.com")
        self.client.force_authenticate(operator)
        Menu.objects.all().delete()

        response = self.client.get("/api/menus/")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 8)
        self.assertTrue(any(item["code"] == "customers" for item in response.data))
        self.assertEqual(Menu.objects.count(), len(response.data))

    def test_user_api_can_create_user_with_roles_and_sales_scope(self):
        operator = User.objects.create_superuser(username="root", password="pass123456", email="root@example.com")
        self.client.force_authenticate(operator)
        role = Role.objects.create(name="销售经理", code="sales-manager")
        sales = Person.objects.create(name="许超飞", person_type="sales")
        managed_a = Person.objects.create(name="P1", person_type="sales")
        managed_b = Person.objects.create(name="P2", person_type="sales")

        response = self.client.post("/api/users/", {
            "username": "manager1",
            "email": "manager1@example.com",
            "password": "pass123456",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "role_ids": [role.id],
            "bound_person_id": sales.id,
            "data_scope_type": UserAccessProfile.DATA_SCOPE_CUSTOM,
            "sales_scope_ids": [managed_a.id, managed_b.id],
        }, format="json")

        self.assertEqual(response.status_code, 201)
        created = User.objects.get(username="manager1")
        self.assertTrue(created.check_password("pass123456"))
        self.assertEqual(created.user_roles.first().role_id, role.id)
        self.assertEqual(created.person_profile.id, sales.id)
        self.assertEqual(created.access_profile.data_scope_type, UserAccessProfile.DATA_SCOPE_CUSTOM)
        self.assertCountEqual(
            list(created.access_profile.sales_scopes.values_list("sales_person_id", flat=True)),
            [managed_a.id, managed_b.id],
        )


    def test_token_activity_is_refreshed_by_authenticated_request(self):
        from datetime import timedelta

        from django.utils import timezone
        from rest_framework.authtoken.models import Token

        from accounts.models import TokenActivity

        user = User.objects.create_user(username="active-token-user", password="pass123456")
        token = Token.objects.create(user=user)
        previous_activity = timezone.now() - timedelta(minutes=5)
        activity = TokenActivity.objects.create(token=token, last_active_at=previous_activity)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        activity.refresh_from_db()
        self.assertGreater(activity.last_active_at, previous_activity)

    def test_idle_token_is_rejected_after_thirty_minutes(self):
        from datetime import timedelta

        from django.utils import timezone
        from rest_framework.authtoken.models import Token

        from accounts.models import TokenActivity

        user = User.objects.create_user(username="expired-token-user", password="pass123456")
        token = Token.objects.create(user=user)
        TokenActivity.objects.create(token=token, last_active_at=timezone.now() - timedelta(minutes=31))
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Token.objects.filter(key=token.key).exists())


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
