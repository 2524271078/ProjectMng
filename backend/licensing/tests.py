import base64
import json
import tempfile
from datetime import date, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APITestCase

from licensing.services import canonical_payload, get_machine_fingerprint


class LicenseApiTests(APITestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.public_key_path = Path(self.tempdir.name) / "public_key.pem"
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key_path.write_bytes(self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
        self.override = override_settings(
            LICENSE_ENFORCEMENT_ENABLED=True,
            LICENSE_PUBLIC_KEY_PATH=str(self.public_key_path),
            LICENSE_OPERATOR_USERNAME="xushaotai",
        )
        self.override.enable()
        self.operator = User.objects.create_user(username="xushaotai", password="pass123456")
        self.superuser = User.objects.create_superuser(username="root", password="pass123456", email="root@example.com")

    def tearDown(self):
        self.override.disable()
        self.tempdir.cleanup()

    def envelope(self, expires_at=None):
        payload = {
            "version": 1,
            "license_id": "license-test-001",
            "customer": "测试客户",
            "issued_at": date.today().isoformat(),
            "expires_at": (expires_at or date.today() + timedelta(days=180)).isoformat(),
            "machine_fingerprint": get_machine_fingerprint(),
        }
        return {
            "algorithm": "Ed25519",
            "payload": payload,
            "signature": base64.b64encode(self.private_key.sign(canonical_payload(payload))).decode("ascii"),
        }

    def test_only_named_user_can_manage_license(self):
        self.client.force_authenticate(self.superuser)
        self.assertEqual(self.client.get("/api/license/").status_code, 403)
        self.client.force_authenticate(self.operator)
        status = self.client.get("/api/license/")
        self.assertEqual(status.status_code, 200)
        self.assertFalse(status.data["active"])

    def test_valid_signed_license_unlocks_business_api(self):
        self.client.force_authenticate(self.operator)
        blocked = self.client.get("/api/dashboard-overview/")
        self.assertEqual(blocked.status_code, 423)
        activated = self.client.post("/api/license/activate/", {"license": self.envelope()}, format="json")
        self.assertEqual(activated.status_code, 200)
        self.assertTrue(activated.data["active"])
        allowed = self.client.get("/api/dashboard-overview/")
        self.assertNotEqual(allowed.status_code, 423)

    def test_expired_license_cannot_be_activated(self):
        self.client.force_authenticate(self.operator)
        response = self.client.post(
            "/api/license/activate/",
            {"license": self.envelope(date.today() - timedelta(days=1))},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_machine_fingerprint_is_part_of_signed_payload(self):
        self.client.force_authenticate(self.operator)
        license_data = self.envelope()
        license_data["payload"]["machine_fingerprint"] = "other-machine"
        response = self.client.post("/api/license/activate/", {"license": license_data}, format="json")
        self.assertEqual(response.status_code, 400)
