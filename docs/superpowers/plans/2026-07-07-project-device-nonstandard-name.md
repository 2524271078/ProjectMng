# Project Device Nonstandard Name Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional nonstandard-name field for nonstandard project devices and remove customer-contact/sales fields from the project-device detail display.

**Architecture:** Persist the new value on the shared `Device` model because both “new device” and “select existing device” flows update device data directly. Surface the field through existing serializers and form payload helpers, then trim the project detail drawer presentation in the frontend without changing list behavior.

**Tech Stack:** Django, Django REST Framework, Vue 3, Element Plus, Node test runner, Django test runner

---

### Task 1: Define backend persistence for nonstandard device names

**Files:**
- Modify: `backend/projects/tests.py`
- Modify: `backend/projects/models.py`
- Create: `backend/projects/migrations/0007_device_nonstandard_name.py`

- [ ] **Step 1: Write the failing backend API test**

```python
def test_device_api_accepts_optional_nonstandard_name_for_nonstandard_product(self):
    product = Product.objects.create(name="Nonstandard Product", product_code="NONSTANDARD-P")
    model = DeviceModel.objects.create(product=product, model_name="NONSTANDARD-1000", model_code="NONSTANDARD-1000")

    response = self.client.post("/api/devices/", {
        "name": "Custom Device",
        "serial_number": "NONSTANDARD-SN-001",
        "device_model": model.id,
        "is_standard_product": False,
        "nonstandard_name": "Customer Specific Variant",
    }, format="json")

    self.assertEqual(response.status_code, 201)
    self.assertEqual(response.data["nonstandard_name"], "Customer Specific Variant")
```

- [ ] **Step 2: Run the backend test to verify it fails**

Run: `python manage.py test backend.projects.tests.DeviceApiNonstandardNameTests`
Expected: `FAIL` because `nonstandard_name` does not exist on the `Device` model/serializer yet.

- [ ] **Step 3: Add the model field and migration**

```python
class Device(BaseModel):
    ...
    is_standard_product = models.BooleanField(default=True, db_index=True)
    nonstandard_name = models.CharField(max_length=200, blank=True, default="")
    supports_remote = models.BooleanField(default=False, db_index=True)
    ...
```

```python
class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0006_project_contact_company_project_winning_company"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="nonstandard_name",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
```

- [ ] **Step 4: Run the backend test to verify it passes**

Run: `python manage.py test backend.projects.tests.DeviceApiNonstandardNameTests`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/projects/models.py backend/projects/migrations/0007_device_nonstandard_name.py backend/projects/tests.py
git commit -m "feat: support nonstandard project device names"
```

### Task 2: Add frontend form support for the optional field

**Files:**
- Modify: `frontend/src/utils/projectDeviceForm.test.js`
- Modify: `frontend/src/utils/projectDeviceForm.js`
- Modify: `frontend/src/views/DeviceCenterView.vue`

- [ ] **Step 1: Write the failing frontend payload test**

```javascript
test('buildProjectDevicePayload keeps optional nonstandard name for nonstandard devices', () => {
  const payload = buildProjectDevicePayload(
    {
      device_name: 'Custom Device',
      serial_number: 'NONSTANDARD-SN-001',
      device_model: 7,
      nonstandard_name: 'Customer Specific Variant',
    },
    {
      customerOrgId: 11,
      salesPersonId: 22,
    },
  )

  assert.equal(payload.nonstandard_name, 'Customer Specific Variant')
})
```

- [ ] **Step 2: Run the frontend test to verify it fails**

Run: `node --test frontend/src/utils/projectDeviceForm.test.js`
Expected: `FAIL` because the payload helper does not include `nonstandard_name` yet.

- [ ] **Step 3: Implement the minimal frontend changes**

```javascript
export function createDefaultProjectDeviceForm() {
  return {
    ...
    is_standard_product: true,
    nonstandard_name: '',
    ...
  }
}

export function buildProjectDevicePayload(form, { customerOrgId, salesPersonId }) {
  return {
    name: form.device_name,
    serial_number: form.serial_number,
    device_model: parseProductModelTreeValue(form.device_model),
    customer_org: customerOrgId ?? null,
    sales_person: salesPersonId ?? null,
    nonstandard_name: form.nonstandard_name?.trim() || '',
  }
}
```

```vue
<el-col v-if="!deviceBinding.is_standard_product" :span="12">
  <el-form-item label="非标名称">
    <el-input v-model="deviceBinding.nonstandard_name" placeholder="请输入非标名称" />
  </el-form-item>
</el-col>
```

```javascript
await updateResource('devices', deviceId, {
  ...
  is_standard_product: deviceBinding.is_standard_product,
  nonstandard_name: deviceBinding.nonstandard_name?.trim() || '',
  ...
})
```

- [ ] **Step 4: Run the frontend test to verify it passes**

Run: `node --test frontend/src/utils/projectDeviceForm.test.js`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/projectDeviceForm.js frontend/src/utils/projectDeviceForm.test.js frontend/src/views/DeviceCenterView.vue
git commit -m "feat: collect nonstandard project device names"
```

### Task 3: Trim project-device detail presentation and verify end-to-end behavior

**Files:**
- Modify: `backend/projects/tests.py`
- Modify: `frontend/src/views/DeviceCenterView.vue`

- [ ] **Step 1: Write the failing backend overview test for the field**

```python
def test_project_overview_device_detail_includes_nonstandard_name(self):
    customer = Organization.objects.create(name="Overview Customer", org_type="customer")
    product = Product.objects.create(name="Overview Product", product_code="OVERVIEW-P")
    model = DeviceModel.objects.create(product=product, model_name="OVERVIEW-1000", model_code="OVERVIEW-1000")
    device = Device.objects.create(
        name="Overview Device",
        serial_number="OVERVIEW-SN-001",
        device_model=model,
        customer_org=customer,
        is_standard_product=False,
        nonstandard_name="Customer Specific Variant",
    )
    project = Project.objects.create(project_no="OVERVIEW-PRJ-001", name="Overview Project", customer_org=customer)
    ProjectDevice.objects.create(project=project, device=device, service_type="renewal")

    response = self.client.get(f"/api/projects/{project.id}/overview/")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data["devices"][0]["nonstandard_name"], "Customer Specific Variant")
```

- [ ] **Step 2: Run the backend overview test to verify it fails**

Run: `python manage.py test backend.projects.tests.ProjectOverviewDeviceNonstandardNameTests`
Expected: `FAIL` because the overview payload does not expose the field yet.

- [ ] **Step 3: Implement minimal presentation changes**

```vue
<el-descriptions-item v-if="selectedDevice && !selectedDevice.is_standard_product" label="非标名称">
  {{ selectedDevice.nonstandard_name || '-' }}
</el-descriptions-item>
```

Remove these detail rows from the project-device detail drawer:

```vue
<el-descriptions-item label="客户联系人">...</el-descriptions-item>
<el-descriptions-item label="销售">...</el-descriptions-item>
```

Ensure edit/fill flows preserve:

```javascript
nonstandard_name: device.nonstandard_name || ''
```

- [ ] **Step 4: Run focused verification**

Run: `python manage.py test backend.projects.tests.DeviceApiNonstandardNameTests backend.projects.tests.ProjectOverviewDeviceNonstandardNameTests`
Expected: `OK`

Run: `node --test frontend/src/utils/projectDeviceForm.test.js frontend/src/utils/projectDeviceForm.normalization.test.js`
Expected: all tests `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/projects/tests.py frontend/src/views/DeviceCenterView.vue
git commit -m "refactor: simplify project device detail display"
```
