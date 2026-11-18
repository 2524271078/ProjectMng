from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core import mail
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from openpyxl import load_workbook

from projects.models import Device, DeviceModel, Organization, Person, Product, Project, ProjectDevice, ServiceExpiryEmailRecord, ServiceExpiryEmailSetting


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="delivery@example.com",
)
class ServiceExpiryEmailApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="expiry-email", password="pass123456")
        self.client.force_authenticate(self.user)
        self.customer = Organization.objects.create(name="到期提醒客户", org_type="customer")
        self.sales = Person.objects.create(name="张三", person_type="sales", email="sales@example.com")
        product = Product.objects.create(name="到期提醒产品")
        model = DeviceModel.objects.create(product=product, model_name="提醒设备型号")
        self.device = Device.objects.create(name="提醒设备", serial_number="EXPIRY-001", device_model=model)
        self.project = Project.objects.create(
            project_no="EXPIRY-PROJECT-001",
            name="到期提醒项目",
            customer_org=self.customer,
            sales_person=self.sales,
        )
        self.binding = ProjectDevice.objects.create(
            project=self.project,
            device=self.device,
            service_start_date=timezone.localdate() - timedelta(days=100),
            service_end_date=timezone.localdate() + timedelta(days=100),
        )

    def test_list_includes_device_expiring_within_six_months(self):
        response = self.client.get("/api/expiry-email-reminders/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["delivery_status"], "pending")
        self.assertEqual(response.data["results"][0]["sales_email"], "sales@example.com")

    def test_same_service_period_is_only_sent_once(self):
        first = self.client.post(
            "/api/expiry-email-reminders/",
            {"project_device_ids": [self.binding.id]},
            format="json",
        )
        second = self.client.post(
            "/api/expiry-email-reminders/",
            {"project_device_ids": [self.binding.id]},
            format="json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["sent"], 1)
        self.assertEqual(second.data["skipped"], 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].attachments), 1)
        attachment = mail.outbox[0].attachments[0]
        self.assertTrue(attachment.filename.endswith(".xlsx"))
        workbook = load_workbook(BytesIO(attachment.content), read_only=True)
        sheet = workbook["维保到期设备"]
        self.assertEqual(sheet["A1"].value, "维保到期设备清单")
        self.assertEqual(sheet["F5"].value, "EXPIRY-001")
        self.assertEqual(sheet["C4"].value, "项目名称")
        self.assertNotIn("项目编号", [cell.value for cell in sheet[4]])
        self.assertNotIn("销售邮箱", [cell.value for cell in sheet[4]])
        record = ServiceExpiryEmailRecord.objects.get(project_device=self.binding)
        self.assertEqual(record.status, ServiceExpiryEmailRecord.STATUS_SENT)

    def test_sent_record_can_be_explicitly_resent(self):
        payload = {"project_device_ids": [self.binding.id]}
        self.client.post("/api/expiry-email-reminders/", payload, format="json")

        response = self.client.post(
            "/api/expiry-email-reminders/",
            {**payload, "force_resend": True},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sent"], 1)
        self.assertEqual(len(mail.outbox), 2)
        record = ServiceExpiryEmailRecord.objects.get(project_device=self.binding)
        self.assertEqual(record.attempt_count, 2)

    def test_configured_addresses_are_cced_without_duplicating_primary_recipient(self):
        ServiceExpiryEmailSetting.objects.create(
            cc_emails=["manager@example.com", "sales@example.com", "MANAGER@example.com"],
        )

        response = self.client.post(
            "/api/expiry-email-reminders/",
            {"project_device_ids": [self.binding.id]},
            format="json",
        )

        self.assertEqual(response.data["sent"], 1)
        self.assertEqual(mail.outbox[0].to, ["sales@example.com"])
        self.assertEqual(mail.outbox[0].cc, ["manager@example.com"])

    def test_only_superuser_can_update_cc_settings(self):
        forbidden = self.client.put(
            "/api/expiry-email-settings/",
            {"cc_emails": ["manager@example.com"]},
            format="json",
        )
        self.assertEqual(forbidden.status_code, 403)

        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save(update_fields=["is_superuser", "is_staff"])
        response = self.client.put(
            "/api/expiry-email-settings/",
            {"cc_emails": ["manager@example.com", "MANAGER@example.com"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cc_emails"], ["manager@example.com"])

    def test_missing_sales_email_is_reported_and_can_be_retried(self):
        self.sales.email = ""
        self.sales.save(update_fields=["email"])

        response = self.client.post(
            "/api/expiry-email-reminders/",
            {"project_device_ids": [self.binding.id]},
            format="json",
        )

        self.assertEqual(response.data["failed"], 1)
        record = ServiceExpiryEmailRecord.objects.get(project_device=self.binding)
        self.assertEqual(record.status, ServiceExpiryEmailRecord.STATUS_FAILED)
        self.assertIn("邮箱", record.last_error)

    def test_batch_send_groups_multiple_devices_for_same_salesperson_into_one_email(self):
        second_device = Device.objects.create(
            name="提醒设备二",
            serial_number="EXPIRY-002",
            device_model=self.device.device_model,
        )
        second_binding = ProjectDevice.objects.create(
            project=self.project,
            device=second_device,
            service_start_date=timezone.localdate() - timedelta(days=50),
            service_end_date=timezone.localdate() + timedelta(days=120),
        )

        response = self.client.post("/api/expiry-email-reminders/", {}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sent"], 2)
        self.assertEqual(response.data["emails_sent"], 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("2 台", mail.outbox[0].subject)
        self.assertIn("张总，您好", mail.outbox[0].body)
        self.assertIn("2 台设备", mail.outbox[0].body)
        self.assertIn("到期提醒客户：提醒设备型号（2 台）", mail.outbox[0].body)
        self.assertIn("具体设备及维保到期信息请查看邮件附件", mail.outbox[0].body)
        self.assertNotIn("EXPIRY-001", mail.outbox[0].body)
        self.assertNotIn("EXPIRY-002", mail.outbox[0].body)
        attachment = mail.outbox[0].attachments[0]
        workbook = load_workbook(BytesIO(attachment.content), read_only=True)
        sheet = workbook["维保到期设备"]
        self.assertEqual(sheet.max_row, 6)
        self.assertEqual(sheet.max_column, 10)
        self.assertEqual({sheet["F5"].value, sheet["F6"].value}, {"EXPIRY-001", "EXPIRY-002"})
        self.assertEqual(
            ServiceExpiryEmailRecord.objects.filter(
                project_device__in=[self.binding, second_binding],
                status=ServiceExpiryEmailRecord.STATUS_SENT,
            ).count(),
            2,
        )

        resend_response = self.client.post(
            "/api/expiry-email-reminders/",
            {"force_resend": True, "resend_sent_only": True},
            format="json",
        )
        self.assertEqual(resend_response.data["emails_sent"], 1)
        self.assertEqual(resend_response.data["sent"], 2)
        self.assertEqual(len(mail.outbox), 2)
