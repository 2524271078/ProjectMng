from django.test import TestCase


class RootEndpointTests(TestCase):
    def test_root_endpoint_returns_service_metadata(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "项目设备管理系统 API")
        self.assertEqual(response.json()["api_base"], "/api/")
