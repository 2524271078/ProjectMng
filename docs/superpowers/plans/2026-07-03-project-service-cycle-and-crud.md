# Project Service Cycle And CRUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add project-device service cycle management, current in-warranty status derivation, and full project-center CRUD for projects, project devices, and project attachments.

**Architecture:** Store service-cycle history directly on `ProjectDevice` so each project-device relationship can represent either a new installation or a renewal without overwriting older records. Derive the current device service status from the latest effective `ProjectDevice` entry, then surface that status consistently in the project center, customer center, and device-detail views while completing CRUD actions around the existing project workflow.

**Tech Stack:** Django, Django REST Framework, SQLite migrations, Vue 3, Element Plus, axios, node:test

---

## File Structure

**Backend**

- Modify: `backend/projects/models.py`
  - Add service-cycle fields to `ProjectDevice`
- Modify: `backend/projects/serializers.py`
  - Expose new `ProjectDevice` fields
- Modify: `backend/projects/views.py`
  - Compute current device service status
  - Add project update/delete support via existing viewsets
  - Add attachment delete behavior if missing from the frontend flow
- Modify: `backend/projects/tests.py`
  - Cover service-cycle storage and current-status derivation
  - Cover project soft delete and project-device record behavior
- Create: `backend/projects/migrations/<timestamp>_projectdevice_service_cycle.py`

**Frontend**

- Modify: `frontend/src/views/DeviceCenterView.vue`
  - Add project edit/delete UI
  - Add project-device mode selection for new install vs renewal
  - Add project-device edit/delete UI
  - Add project attachment delete UI
- Modify: `frontend/src/views/CustomerCenterView.vue`
  - Show current warranty/service status in device lists and device detail
- Modify: `frontend/src/api/resources.js`
  - Add helpers for project-device update/delete and attachment delete if useful
- Modify: `frontend/src/utils/projectDeviceForm.js`
  - Add service-cycle defaults and payload helpers
- Modify: `frontend/src/utils/projectDeviceForm.test.js`
  - Cover service-cycle payload and mode behavior
- Modify: `frontend/src/utils/displayMaps.js`
  - Add service-type/service-status label helpers if needed
- Modify: `frontend/src/utils/displayMaps.test.js`
  - Cover label mapping behavior

### Task 1: Add backend tests for project-device service cycles

**Files:**
- Modify: `backend/projects/tests.py`
- Test: `backend/projects/tests.py`

- [ ] **Step 1: Write the failing model/API test for service-cycle fields**

```python
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
```

- [ ] **Step 2: Write the failing current-status derivation test**

```python
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
        ProjectDevice.objects.create(project=project_new, device=device, service_type="renewal", service_start_date="2026-01-01", service_end_date="2027-12-31")

        response = self.client.get(f"/api/devices/{device.id}/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["device"]["current_service_status"], "保内")
        self.assertEqual(response.data["device"]["current_service_end_date"], "2027-12-31")
```

- [ ] **Step 3: Run the targeted tests and verify they fail**

Run:

```powershell
cd backend
python manage.py test projects.tests.ProjectDeviceServiceCycleTests projects.tests.DeviceCurrentServiceStatusTests
```

Expected: `FAIL` because the new fields and derived response data do not exist yet.

- [ ] **Step 4: Commit the failing-test checkpoint**

```bash
git add backend/projects/tests.py
git commit -m "测试：补充项目设备服务周期用例"
```

### Task 2: Add service-cycle fields and current-status derivation to the backend

**Files:**
- Modify: `backend/projects/models.py`
- Modify: `backend/projects/serializers.py`
- Modify: `backend/projects/views.py`
- Create: `backend/projects/migrations/<timestamp>_projectdevice_service_cycle.py`
- Test: `backend/projects/tests.py`

- [ ] **Step 1: Add the new fields to `ProjectDevice`**

```python
class ProjectDevice(BaseModel):
    project = models.ForeignKey(Project, related_name="project_devices", on_delete=models.CASCADE)
    device = models.ForeignKey(Device, related_name="project_devices", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    deploy_location = models.CharField(max_length=200, blank=True, default="")
    device_project_type = models.CharField(max_length=100, blank=True, default="")
    usage = models.CharField(max_length=200, blank=True, default="")
    service_type = models.CharField(max_length=32, default="new_install", db_index=True)
    service_start_date = models.DateField(null=True, blank=True)
    service_end_date = models.DateField(null=True, blank=True)
```

- [ ] **Step 2: Expose the fields through serializers**

```python
class ProjectDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDevice
        fields = "__all__"
```

- [ ] **Step 3: Add a service-status helper in `views.py`**

```python
from django.utils import timezone

def latest_project_device_service(device):
    return (
        device.project_devices.filter(is_deleted=False, service_end_date__isnull=False)
        .order_by("-service_end_date", "-updated_at", "-id")
        .first()
    )

def service_status_from_binding(binding):
    if not binding or not binding.service_start_date or not binding.service_end_date:
        return "保外"
    today = timezone.localdate()
    return "保内" if binding.service_start_date <= today <= binding.service_end_date else "保外"
```

- [ ] **Step 4: Extend device/customer/project overview payloads**

```python
def device_summary(device):
    latest_binding = latest_project_device_service(device)
    return {
        "id": device.id,
        "name": device.name,
        "serial_number": device.serial_number,
        "hardware_code": device.hardware_code,
        "management_address": device.management_address,
        "version_update_method": device.version_update_method,
        "is_standard_product": device.is_standard_product,
        "supports_remote": device.supports_remote,
        "software_version": device.software_version,
        "rule_library_version": device.rule_library_version,
        "license_info": device.license_info,
        "is_under_warranty": service_status_from_binding(latest_binding) == "保内",
        "current_service_status": service_status_from_binding(latest_binding),
        "current_service_start_date": latest_binding.service_start_date.isoformat() if latest_binding and latest_binding.service_start_date else None,
        "current_service_end_date": latest_binding.service_end_date.isoformat() if latest_binding and latest_binding.service_end_date else None,
        "screenshot_url": device.screenshot_url,
        "rack_install_date": device.rack_install_date.isoformat() if device.rack_install_date else None,
        "ops_person": person_summary(device.ops_person),
        "remark": device.remark,
        "status": device.status,
    }
```

```python
"devices": [
    {
        **device_summary(binding.device),
        "quantity": binding.quantity,
        "deploy_location": binding.deploy_location,
        "device_project_type": binding.device_project_type,
        "usage": binding.usage,
        "service_type": binding.service_type,
        "service_start_date": binding.service_start_date.isoformat() if binding.service_start_date else None,
        "service_end_date": binding.service_end_date.isoformat() if binding.service_end_date else None,
        "service_status": service_status_from_binding(binding),
    }
    for binding in bindings
]
```

- [ ] **Step 5: Create the migration and run the targeted tests**

Run:

```powershell
cd backend
python manage.py makemigrations projects
python manage.py test projects.tests.ProjectDeviceServiceCycleTests projects.tests.DeviceCurrentServiceStatusTests
```

Expected: migration created and targeted tests `OK`.

- [ ] **Step 6: Commit the backend service-cycle module**

```bash
git add backend/projects/models.py backend/projects/serializers.py backend/projects/views.py backend/projects/tests.py backend/projects/migrations
git commit -m "后端：新增项目设备服务周期能力"
```

### Task 3: Add project CRUD coverage and backend support

**Files:**
- Modify: `backend/projects/tests.py`
- Modify: `backend/projects/views.py`

- [ ] **Step 1: Write the failing project edit/delete API test**

```python
class ProjectCrudApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="project-crud", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_project_can_be_updated_and_soft_deleted(self):
        project = Project.objects.create(project_no="CRUD-PRJ-001", name="原项目名称")

        update = self.client.patch(f"/api/projects/{project.id}/", {"name": "更新后项目名称"}, format="json")
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data["name"], "更新后项目名称")

        delete = self.client.delete(f"/api/projects/{project.id}/")
        self.assertEqual(delete.status_code, 204)

        project.refresh_from_db()
        self.assertTrue(project.is_deleted)
```

- [ ] **Step 2: Run the targeted CRUD test**

Run:

```powershell
cd backend
python manage.py test projects.tests.ProjectCrudApiTests
```

Expected: if project update/delete handling is incomplete, the test fails for the expected reason.

- [ ] **Step 3: Adjust backend behavior only if the test proves it is needed**

Possible minimal code if needed:

```python
class ProjectViewSet(SoftDeleteModelViewSet):
    queryset = Project.objects.select_related("customer_org", "customer_contact", "sales_person", "ops_person").all().order_by("id")
    serializer_class = ProjectSerializer
```

- [ ] **Step 4: Run the targeted CRUD test again**

Run:

```powershell
cd backend
python manage.py test projects.tests.ProjectCrudApiTests
```

Expected: `OK`.

- [ ] **Step 5: Commit the project CRUD backend module**

```bash
git add backend/projects/views.py backend/projects/tests.py
git commit -m "后端：补充项目增删改接口校验"
```

### Task 4: Add frontend utilities for service-cycle data entry

**Files:**
- Modify: `frontend/src/utils/projectDeviceForm.js`
- Modify: `frontend/src/utils/projectDeviceForm.test.js`
- Modify: `frontend/src/utils/displayMaps.js`
- Modify: `frontend/src/utils/displayMaps.test.js`

- [ ] **Step 1: Write the failing utility tests**

```javascript
test('default project device form includes service-cycle fields', () => {
  const form = createDefaultProjectDeviceForm()

  assert.equal(form.service_type, 'new_install')
  assert.equal(form.service_start_date, '')
  assert.equal(form.service_end_date, '')
})

test('buildProjectDevicePayload includes service-cycle fields', () => {
  const payload = buildProjectDevicePayload(
    {
      device_name: '项目设备',
      serial_number: 'PJ-SN-001',
      device_model: 7,
      service_start_date: '2026-07-01',
      service_end_date: '2027-06-30',
    },
    {
      customerOrgId: 11,
      salesPersonId: 22,
    },
  )

  assert.equal(payload.service_start_date, '2026-07-01')
  assert.equal(payload.service_end_date, '2027-06-30')
})
```

```javascript
test('serviceTypeLabel maps service types to Chinese labels', () => {
  assert.equal(serviceTypeLabel('new_install'), '新上设备')
  assert.equal(serviceTypeLabel('renewal'), '续保旧设备')
})
```

- [ ] **Step 2: Run the utility tests and verify they fail**

Run:

```powershell
cd frontend
node --test src/utils/projectDeviceForm.test.js src/utils/displayMaps.test.js
```

Expected: `FAIL` because the new defaults and label helper do not exist yet.

- [ ] **Step 3: Implement the minimal utility support**

```javascript
export function createDefaultProjectDeviceForm() {
  return {
    bind_mode: 'new',
    device: null,
    device_model: null,
    device_name: '',
    serial_number: '',
    deploy_location: '',
    device_project_type: '',
    management_address: '',
    hardware_code: '',
    software_version: '',
    version_update_method: '',
    license_info_text: '',
    is_standard_product: true,
    is_under_warranty: false,
    supports_remote: false,
    ops_person: null,
    screenshot_url: '',
    rack_install_date: '',
    remark: '',
    service_type: 'new_install',
    service_start_date: '',
    service_end_date: '',
  }
}
```

```javascript
export function serviceTypeLabel(value) {
  return { new_install: '新上设备', renewal: '续保旧设备' }[value] || value || '-'
}
```

- [ ] **Step 4: Re-run the utility tests**

Run:

```powershell
cd frontend
node --test src/utils/projectDeviceForm.test.js src/utils/displayMaps.test.js
```

Expected: `OK`.

- [ ] **Step 5: Commit the frontend utility module**

```bash
git add frontend/src/utils/projectDeviceForm.js frontend/src/utils/projectDeviceForm.test.js frontend/src/utils/displayMaps.js frontend/src/utils/displayMaps.test.js
git commit -m "前端：补充服务周期表单与展示映射"
```

### Task 5: Add project-center CRUD and service-cycle UX

**Files:**
- Modify: `frontend/src/views/DeviceCenterView.vue`
- Modify: `frontend/src/api/resources.js`

- [ ] **Step 1: Add project list actions for edit/delete**

```vue
<el-table-column label="操作" width="180" fixed="right">
  <template #default="scope">
    <el-button link type="primary" @click.stop="openDetail(scope.row)">详情</el-button>
    <el-button link type="primary" @click.stop="openEditProject(scope.row)">编辑</el-button>
    <el-button link type="danger" @click.stop="removeProject(scope.row)">删除</el-button>
  </template>
</el-table-column>
```

- [ ] **Step 2: Add the failing form-flow check via build validation**

Manual expected behavior before implementation:

```text
1. 项目设备表单应新增“新上设备 / 续保旧设备”选择
2. 表单应显示服务开始日期和服务结束日期
3. 续保模式应只能从当前客户已有设备里选择
4. 项目设备列表应有编辑和删除操作
5. 项目附件列表应有删除操作
```

- [ ] **Step 3: Implement project CRUD and project-device CRUD UI**

Required code additions:

```javascript
const editingProjectId = ref(null)
const editingProjectDevice = ref(null)

async function openEditProject(row) {
  editingProjectId.value = row.id
  Object.assign(form, {
    project_no: row.project_no || '',
    name: row.name || '',
    customer_org: row.customer_org || null,
    customer_contact: row.customer_contact || null,
    winning_company: row.winning_company || '',
    contact_company: row.contact_company || '',
    sales_person: row.sales_person || null,
    project_stage: row.project_stage || 'new',
    amount: Number(row.amount || 0),
  })
  await loadCustomerContacts(form.customer_org)
  dialogVisible.value = true
}

async function removeProject(row) {
  await ElMessageBox.confirm(`确认删除项目“${row.name}”？`, '删除确认', { type: 'warning' })
  await deleteResource('projects', row.id)
  ElMessage.success('项目已删除')
  await loadProjects()
}
```

```javascript
async function saveProject() {
  if (editingProjectId.value) {
    await updateResource('projects', editingProjectId.value, form)
  } else {
    await createResource('projects', form)
  }
}
```

```javascript
async function removeProjectDevice(row) {
  await deleteResource('project-devices', row.id)
  ElMessage.success('项目设备已删除')
  await openDetail({ id: activeProjectId.value })
}
```

- [ ] **Step 4: Add service-cycle fields to the project-device form and payload**

```vue
<el-col :span="12">
  <el-form-item label="服务类型">
    <el-radio-group v-model="deviceBinding.service_type">
      <el-radio-button label="new_install">新上设备</el-radio-button>
      <el-radio-button label="renewal">续保旧设备</el-radio-button>
    </el-radio-group>
  </el-form-item>
</el-col>
<el-col :span="12">
  <el-form-item label="服务开始日期" required>
    <el-date-picker v-model="deviceBinding.service_start_date" type="date" value-format="YYYY-MM-DD" />
  </el-form-item>
</el-col>
<el-col :span="12">
  <el-form-item label="服务结束日期" required>
    <el-date-picker v-model="deviceBinding.service_end_date" type="date" value-format="YYYY-MM-DD" />
  </el-form-item>
</el-col>
```

```javascript
await createResource('project-devices', {
  project: activeProjectId.value,
  device: deviceId,
  quantity: 1,
  deploy_location: deviceBinding.deploy_location,
  device_project_type: deviceBinding.device_project_type,
  service_type: deviceBinding.service_type,
  service_start_date: deviceBinding.service_start_date,
  service_end_date: deviceBinding.service_end_date,
})
```

- [ ] **Step 5: Add attachment delete UI**

```vue
<el-button
  v-if="scope.row.id"
  link
  type="danger"
  @click.stop="removeProjectAttachment(scope.row)"
>
  删除
</el-button>
```

```javascript
async function removeProjectAttachment(row) {
  await deleteResource('attachments', row.id)
  ElMessage.success('附件已删除')
  await openDetail({ id: activeProjectId.value })
}
```

- [ ] **Step 6: Run the frontend build and utility tests**

Run:

```powershell
cd frontend
node --test src/utils/*.test.js
npm run build
```

Expected: both commands pass.

- [ ] **Step 7: Commit the project-center CRUD module**

```bash
git add frontend/src/views/DeviceCenterView.vue frontend/src/api/resources.js
git commit -m "前端：完善项目中心增删改和服务周期录入"
```

### Task 6: Surface current service status in customer-center and device detail views

**Files:**
- Modify: `frontend/src/views/CustomerCenterView.vue`

- [ ] **Step 1: Add current service status fields to the customer device list**

```vue
<el-table-column prop="current_service_status" label="保内保外" min-width="120" />
<el-table-column prop="current_service_end_date" label="服务到期日" min-width="140" />
```

- [ ] **Step 2: Add service-cycle detail to the shared device detail dialog**

```vue
<el-descriptions-item label="当前服务状态">{{ selectedDevice.current_service_status || '-' }}</el-descriptions-item>
<el-descriptions-item label="服务开始日期">{{ selectedDevice.current_service_start_date || '-' }}</el-descriptions-item>
<el-descriptions-item label="服务结束日期">{{ selectedDevice.current_service_end_date || '-' }}</el-descriptions-item>
```

- [ ] **Step 3: Add service-cycle fields to the customer project-device table**

```vue
<el-table-column prop="service_type" label="服务类型" min-width="120">
  <template #default="scope">{{ serviceTypeLabel(scope.row.service_type) }}</template>
</el-table-column>
<el-table-column prop="service_start_date" label="服务开始日期" min-width="140" />
<el-table-column prop="service_end_date" label="服务结束日期" min-width="140" />
<el-table-column prop="service_status" label="保内保外" min-width="120" />
```

- [ ] **Step 4: Run the frontend build**

Run:

```powershell
cd frontend
npm run build
```

Expected: `vite build` succeeds.

- [ ] **Step 5: Commit the customer-center service-status module**

```bash
git add frontend/src/views/CustomerCenterView.vue
git commit -m "前端：展示设备当前服务周期和保内状态"
```

### Task 7: Run the full verification sweep

**Files:**
- Modify: `docs/superpowers/specs/2026-07-03-project-service-cycle-and-crud-design.md` (only if implementation diverged)
- Modify: `docs/superpowers/plans/2026-07-03-project-service-cycle-and-crud.md` (only if sequencing changed)

- [ ] **Step 1: Run the backend test suite**

Run:

```powershell
cd backend
python manage.py test
```

Expected: `OK`.

- [ ] **Step 2: Run the frontend utility tests**

Run:

```powershell
cd frontend
node --test src/utils/*.test.js
```

Expected: `OK`.

- [ ] **Step 3: Run the frontend production build**

Run:

```powershell
cd frontend
npm run build
```

Expected: build success.

- [ ] **Step 4: Smoke-check the core workflow**

Manual verification checklist:

```text
1. 新建项目并保存。
2. 编辑项目基础信息并保存。
3. 为项目新增一台“新上设备”，填写服务开始/结束日期。
4. 为项目新增一台“续保旧设备”，选择客户已有设备并保存。
5. 在项目详情中确认项目设备列表出现服务类型、服务周期、保内保外。
6. 在客户中心已购设备列表确认当前保内保外和服务到期日。
7. 删除一条项目设备，确认设备主表仍存在。
8. 上传并删除一个项目附件。
9. 删除项目，确认项目软删除后从列表消失。
```

- [ ] **Step 5: Commit any final documentation-only adjustments**

```bash
git add docs
git commit -m "文档：补充项目服务周期与项目中心 CRUD 方案"
```

## Self-Review

- Spec coverage:
  - 服务周期记在 `ProjectDevice`：Task 1 and Task 2
  - 当前保内保外取最近记录：Task 2 and Task 6
  - 新上设备 / 续保旧设备：Task 5
  - 项目中心 CRUD：Task 3 and Task 5
  - 合同文件继续作为项目附件：Task 5
- Placeholder scan:
  - No `TODO`/`TBD` placeholders remain
  - Each task includes explicit files, commands, and code
- Type consistency:
  - `service_type`, `service_start_date`, `service_end_date`, `current_service_status`, `current_service_end_date`, and `service_status` are used consistently
