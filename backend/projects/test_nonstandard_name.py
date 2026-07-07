from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from projects.models import Device, DeviceModel, Organization, Product, Project, ProjectDevice


class DeviceApiNonstandardNameTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='device-nonstandard-name', password='pass123456')
        self.client.force_authenticate(self.user)

    def test_device_api_accepts_optional_nonstandard_name_for_nonstandard_product(self):
        product = Product.objects.create(name='Nonstandard Product', product_code='NONSTANDARD-P')
        model = DeviceModel.objects.create(product=product, model_name='NONSTANDARD-1000', model_code='NONSTANDARD-1000')

        response = self.client.post('/api/devices/', {
            'name': 'Custom Device',
            'serial_number': 'NONSTANDARD-SN-001',
            'device_model': model.id,
            'is_standard_product': False,
            'nonstandard_name': 'Customer Specific Variant',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nonstandard_name'], 'Customer Specific Variant')


class ProjectOverviewDeviceNonstandardNameTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='project-overview-nonstandard-name', password='pass123456')
        self.client.force_authenticate(self.user)

    def test_project_overview_device_detail_includes_nonstandard_name(self):
        customer = Organization.objects.create(name='Overview Customer', org_type='customer')
        product = Product.objects.create(name='Overview Product', product_code='OVERVIEW-P')
        model = DeviceModel.objects.create(product=product, model_name='OVERVIEW-1000', model_code='OVERVIEW-1000')
        device = Device.objects.create(
            name='Overview Device',
            serial_number='OVERVIEW-SN-001',
            device_model=model,
            customer_org=customer,
            is_standard_product=False,
            nonstandard_name='Customer Specific Variant',
        )
        project = Project.objects.create(project_no='OVERVIEW-PRJ-001', name='Overview Project', customer_org=customer)
        ProjectDevice.objects.create(project=project, device=device, service_type='renewal')

        response = self.client.get(f'/api/projects/{project.id}/overview/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['devices'][0]['nonstandard_name'], 'Customer Specific Variant')

    def test_project_overview_device_detail_uses_readable_warranty_status_labels(self):
        customer = Organization.objects.create(name='Warranty Customer', org_type='customer')
        product = Product.objects.create(name='Warranty Product', product_code='WARRANTY-P')
        model = DeviceModel.objects.create(product=product, model_name='WARRANTY-1000', model_code='WARRANTY-1000')
        device = Device.objects.create(
            name='Warranty Device',
            serial_number='WARRANTY-SN-001',
            device_model=model,
            customer_org=customer,
        )
        project = Project.objects.create(project_no='WARRANTY-PRJ-001', name='Warranty Project', customer_org=customer)
        ProjectDevice.objects.create(
            project=project,
            device=device,
            service_type='renewal',
            service_start_date='2026-07-01',
            service_end_date='2026-07-31',
        )

        response = self.client.get(f'/api/projects/{project.id}/overview/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['devices'][0]['service_status'], '\u4fdd\u5185')
        self.assertEqual(response.data['devices'][0]['current_service_status'], '\u4fdd\u5185')