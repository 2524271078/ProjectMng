from django.contrib.auth.models import User
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase
from types import SimpleNamespace

from projects.models import ServiceExpiryEmailSetting
from projects.services import build_service_expiry_email_content, email_delivery_configured, get_service_expiry_email_config


class ServiceExpiryEmailContentTests(SimpleTestCase):
    def test_email_content_uses_delivery_platform_contact_signature(self):
        binding = SimpleNamespace(
            project=SimpleNamespace(
                sales_person=SimpleNamespace(name="杨销售"),
                customer_org=SimpleNamespace(name="测试客户"),
            ),
            device=SimpleNamespace(
                name="测试设备",
                device_model=SimpleNamespace(model_name="测试型号"),
            ),
        )

        content = build_service_expiry_email_content([binding])

        self.assertTrue(content.endswith("此邮件由交付管理平台发送，如有问题，请联系电力能源交付部杨俊。"))


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    EMAIL_HOST_USER="env-user@example.com",
    EMAIL_HOST_PASSWORD="env-password",
    DEFAULT_FROM_EMAIL="env-from@example.com",
)
class ServiceExpiryEmailSettingsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="email-settings-admin",
            password="pass123456",
            email="admin@example.com",
        )
        self.client.force_authenticate(self.user)

    def test_sender_settings_are_saved_without_returning_password(self):
        response = self.client.put("/api/expiry-email-settings/", {
            "cc_emails": ["copy@example.com"],
            "email_host_user": "smtp-user@example.com",
            "email_host_password": "database-secret",
            "default_from_email": "sender@example.com",
        }, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("email_host_password", response.data)
        self.assertTrue(response.data["email_host_password_set"])

        setting = ServiceExpiryEmailSetting.objects.get(key="default")
        self.assertEqual(setting.email_host_user, "smtp-user@example.com")
        self.assertNotEqual(setting.email_host_password, "database-secret")
        self.assertTrue(setting.email_host_password.startswith("fernet:"))
        self.assertEqual(setting.default_from_email, "sender@example.com")
        self.assertEqual(setting.cc_emails, ["copy@example.com"])

        self.assertEqual(get_service_expiry_email_config(), {
            "email_host_user": "smtp-user@example.com",
            "email_host_password": "database-secret",
            "default_from_email": "sender@example.com",
        })
        self.assertTrue(email_delivery_configured())

    def test_blank_password_keeps_existing_secret(self):
        ServiceExpiryEmailSetting.objects.create(
            key="default",
            email_host_user="old@example.com",
            email_host_password="existing-secret",
            default_from_email="old@example.com",
        )

        response = self.client.put("/api/expiry-email-settings/", {
            "cc_emails": [],
            "email_host_user": "new@example.com",
            "email_host_password": "",
            "default_from_email": "new@example.com",
        }, format="json")

        self.assertEqual(response.status_code, 200)
        setting = ServiceExpiryEmailSetting.objects.get(key="default")
        self.assertEqual(setting.email_host_password, "existing-secret")

        get_response = self.client.get("/api/expiry-email-settings/")
        self.assertEqual(get_response.status_code, 200)
        self.assertNotIn("email_host_password", get_response.data)
        self.assertTrue(get_response.data["email_host_password_set"])
