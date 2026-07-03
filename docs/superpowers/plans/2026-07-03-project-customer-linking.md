# Project Customer Linking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the project center the source of truth for project creation while exposing customer-linked projects, customer-filtered device binding, and explicit project-contract relationships across the backend and frontend.

**Architecture:** Keep the existing `Project.customer_org`, `Project.customer_contact`, and `Project.sales_person` fields as the ownership chain, then extend overview APIs so the customer center can read project data without becoming the authoring surface. Introduce a small `ProjectContract` join model to separate business contract linkage from file attachments, and update the project-center drawer tabs so devices, contracts, and attachments each have clear responsibilities.

**Tech Stack:** Django, Django REST Framework, SQLite migrations, Vue 3, Element Plus, Pinia, axios, node:test

---

## File Structure

**Backend**

- Modify: `backend/projects/models.py`
  - Add the `ProjectContract` model near `ProjectDevice` and `ContractDevice`
- Modify: `backend/projects/serializers.py`
  - Add serializer support for `ProjectContract`
- Modify: `backend/projects/views.py`
  - Expose `ProjectContractViewSet`
  - Extend `customer_overview` with project summaries
  - Extend `project_overview` with contract summaries
- Modify: `backend/config/urls.py`
  - Register the new `/api/project-contracts/` resource
- Modify: `backend/projects/tests.py`
  - Cover customer overview project data
  - Cover project overview contract data
  - Cover project-contract uniqueness

**Frontend**

- Modify: `frontend/src/api/resources.js`
  - Add project-contract API helpers if needed beyond generic CRUD
- Modify: `frontend/src/views/CustomerCenterView.vue`
  - Add the “关联项目” tab and project list interaction
- Modify: `frontend/src/views/DeviceCenterView.vue`
  - Filter device candidates by selected project customer
  - Add contract management UI
  - Split “合同和附件” into separate tabs
- Modify: `frontend/src/utils/projectDeviceForm.js`
  - Add a helper to build customer-owned device payloads
- Modify: `frontend/src/utils/projectDeviceForm.test.js`
  - Cover customer-scoped payload generation

### Task 1: Add backend coverage for customer-project and project-contract overviews

**Files:**
- Modify: `backend/projects/tests.py`
- Test: `backend/projects/tests.py`

- [ ] **Step 1: Write the failing customer-overview project test**

```python
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
```

- [ ] **Step 2: Write the failing project-overview contract test**

```python
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
```

- [ ] **Step 3: Run the targeted tests and verify they fail**

Run:

```powershell
cd backend
python manage.py test projects.tests.CustomerProjectOverviewTests projects.tests.ProjectContractOverviewTests
```

Expected: `FAIL` with missing `projects` or `contracts` response fields and missing `ProjectContract` support.

- [ ] **Step 4: Commit the failing-test checkpoint**

```bash
git add backend/projects/tests.py
git commit -m "test: cover customer project and project contract overviews"
```

### Task 2: Introduce the ProjectContract model and API resource

**Files:**
- Modify: `backend/projects/models.py`
- Modify: `backend/projects/serializers.py`
- Modify: `backend/projects/views.py`
- Modify: `backend/config/urls.py`
- Create: `backend/projects/migrations/<timestamp>_add_project_contract.py`
- Test: `backend/projects/tests.py`

- [ ] **Step 1: Add the failing uniqueness test**

```python
class ProjectContractModelTests(TestCase):
    def test_project_contract_active_relation_is_unique(self):
        customer = Organization.objects.create(name="唯一性客户", org_type="customer")
        project = Project.objects.create(project_no="UNIQ-PRJ-001", name="唯一性项目", customer_org=customer)
        contract = Contract.objects.create(contract_no="UNIQ-CON-001", contract_name="唯一性合同", final_customer=customer)

        ProjectContract.objects.create(project=project, contract=contract)

        with self.assertRaises(Exception):
            ProjectContract.objects.create(project=project, contract=contract)
```

- [ ] **Step 2: Run the new model test and verify it fails**

Run:

```powershell
cd backend
python manage.py test projects.tests.ProjectContractModelTests
```

Expected: `FAIL` because `ProjectContract` does not exist yet.

- [ ] **Step 3: Implement the model, serializer, viewset, and router registration**

```python
class ProjectContract(BaseModel):
    project = models.ForeignKey(Project, related_name="project_contracts", on_delete=models.CASCADE)
    contract = models.ForeignKey(Contract, related_name="project_contracts", on_delete=models.PROTECT)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["project", "contract"],
                condition=models.Q(is_deleted=False),
                name="uniq_active_project_contract",
            )
        ]
```

```python
class ProjectContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContract
        fields = "__all__"
```

```python
class ProjectContractViewSet(SoftDeleteModelViewSet):
    queryset = ProjectContract.objects.select_related("project", "contract").all().order_by("id")
    serializer_class = ProjectContractSerializer
```

```python
router.register("project-contracts", ProjectContractViewSet)
```

- [ ] **Step 4: Create and inspect the migration**

Run:

```powershell
cd backend
python manage.py makemigrations projects
python manage.py sqlmigrate projects <new_migration_number>
```

Expected: a migration adding the `projectcontract` table and the conditional unique constraint.

- [ ] **Step 5: Run the focused backend tests and verify they pass**

Run:

```powershell
cd backend
python manage.py test projects.tests.ProjectContractModelTests projects.tests.ProjectContractOverviewTests
```

Expected: `OK`.

- [ ] **Step 6: Commit the backend join-model work**

```bash
git add backend/projects/models.py backend/projects/serializers.py backend/projects/views.py backend/config/urls.py backend/projects/tests.py backend/projects/migrations
git commit -m "feat: add project contract relationships"
```

### Task 3: Extend overview APIs for customer-linked projects and project-linked contracts

**Files:**
- Modify: `backend/projects/views.py`
- Test: `backend/projects/tests.py`

- [ ] **Step 1: Add a project summary helper**

```python
def project_summary(project):
    return {
        "id": project.id,
        "project_no": project.project_no,
        "name": project.name,
        "project_stage": project.project_stage,
        "amount": str(project.amount),
        "customer_contact": person_summary(project.customer_contact),
        "sales_person": person_summary(project.sales_person),
    }
```

- [ ] **Step 2: Update `customer_overview` to return customer projects**

```python
"projects": [
    project_summary(project)
    for project in customer.projects.select_related("customer_contact", "sales_person").all()
],
```

- [ ] **Step 3: Update `project_overview` to return related contracts**

```python
project_contracts = project.project_contracts.select_related("contract").all()

return Response({
    "project": ProjectSerializer(project).data,
    "customer": organization_summary(project.customer_org) if project.customer_org else None,
    "customer_contact": person_summary(project.customer_contact),
    "sales_person": person_summary(project.sales_person),
    "ops_person": person_summary(project.ops_person),
    "devices": [
        {
            **device_summary(binding.device),
            "quantity": binding.quantity,
            "deploy_location": binding.deploy_location,
            "device_project_type": binding.device_project_type,
            "usage": binding.usage,
        }
        for binding in bindings
    ],
    "contracts": [contract_summary(binding.contract) for binding in project_contracts],
    "attachments": AttachmentSerializer(
        Attachment.objects.filter(object_type="project", object_id=project.id),
        many=True,
        context={"request": request},
    ).data,
})
```

- [ ] **Step 4: Run the targeted overview tests**

Run:

```powershell
cd backend
python manage.py test projects.tests.CustomerProjectOverviewTests projects.tests.ProjectContractOverviewTests
```

Expected: `OK`.

- [ ] **Step 5: Commit the overview API extension**

```bash
git add backend/projects/views.py backend/projects/tests.py
git commit -m "feat: expose customer projects and project contracts"
```

### Task 4: Add customer-center project visibility

**Files:**
- Modify: `frontend/src/views/CustomerCenterView.vue`

- [ ] **Step 1: Add the new “关联项目” tab markup**

```vue
<el-tab-pane label="关联项目" name="projects">
  <el-table :data="overview.projects" @row-click="openProjectDetail">
    <el-table-column prop="project_no" label="项目编号" min-width="150" />
    <el-table-column prop="name" label="项目名称" min-width="220" />
    <el-table-column prop="project_stage" label="阶段" min-width="120" />
    <el-table-column label="销售" min-width="120">
      <template #default="scope">{{ scope.row.sales_person?.name || '-' }}</template>
    </el-table-column>
    <el-table-column prop="amount" label="金额" min-width="120" />
  </el-table>
</el-tab-pane>
```

- [ ] **Step 2: Add project-detail state and interaction**

```vue
<script setup>
import { createResource, deleteResource, fetchCustomerOverview, fetchProjectOverview, listResource, updateResource } from '../api/resources'

const projectDrawerVisible = ref(false)
const projectOverview = ref(null)

async function openProjectDetail(row) {
  const { data } = await fetchProjectOverview(row.id)
  projectOverview.value = data
  projectDrawerVisible.value = true
}
</script>
```

- [ ] **Step 3: Add a simple project drawer**

```vue
<el-drawer v-model="projectDrawerVisible" size="60%" title="项目详情">
  <el-descriptions v-if="projectOverview" :column="2" border>
    <el-descriptions-item label="项目编号">{{ projectOverview.project.project_no }}</el-descriptions-item>
    <el-descriptions-item label="项目名称">{{ projectOverview.project.name }}</el-descriptions-item>
    <el-descriptions-item label="客户公司">{{ projectOverview.customer?.name || '-' }}</el-descriptions-item>
    <el-descriptions-item label="客户联系人">{{ projectOverview.customer_contact?.name || '-' }}</el-descriptions-item>
    <el-descriptions-item label="销售">{{ projectOverview.sales_person?.name || '-' }}</el-descriptions-item>
    <el-descriptions-item label="金额">{{ projectOverview.project.amount }}</el-descriptions-item>
  </el-descriptions>
</el-drawer>
```

- [ ] **Step 4: Verify the customer-center interaction manually**

Run:

```powershell
cd frontend
npm run build
```

Expected: `build` succeeds, and the customer detail panel shows a sixth tab with project rows that open a project drawer.

- [ ] **Step 5: Commit the customer-center update**

```bash
git add frontend/src/views/CustomerCenterView.vue
git commit -m "feat: show customer linked projects"
```

### Task 5: Scope project device binding to the current customer

**Files:**
- Modify: `frontend/src/views/DeviceCenterView.vue`
- Modify: `frontend/src/utils/projectDeviceForm.js`
- Modify: `frontend/src/utils/projectDeviceForm.test.js`

- [ ] **Step 1: Add a failing utility test for customer-owned device payloads**

```javascript
import assert from 'node:assert/strict'
import test from 'node:test'

import { buildProjectDevicePayload } from './projectDeviceForm.js'

test('buildProjectDevicePayload applies current customer and sales ownership', () => {
  const payload = buildProjectDevicePayload(
    {
      device_name: '项目设备',
      serial_number: 'PJ-SN-001',
      device_model: 7,
    },
    {
      customerOrgId: 11,
      salesPersonId: 22,
    },
  )

  assert.equal(payload.customer_org, 11)
  assert.equal(payload.sales_person, 22)
})
```

- [ ] **Step 2: Run the utility test to verify it fails**

Run:

```powershell
cd frontend
node --test src/utils/projectDeviceForm.test.js
```

Expected: `FAIL` because `buildProjectDevicePayload` is not exported yet.

- [ ] **Step 3: Add the helper and wire it into device creation**

```javascript
export function buildProjectDevicePayload(form, { customerOrgId, salesPersonId }) {
  return {
    name: form.device_name,
    serial_number: form.serial_number,
    device_model: form.device_model,
    customer_org: customerOrgId ?? null,
    sales_person: salesPersonId ?? null,
  }
}
```

```javascript
const customerScopedDevices = computed(() =>
  devices.value.filter((device) => {
    if (!overview.value?.customer?.id) return true
    return device.customer_org === overview.value.customer.id
  }),
)
```

```javascript
const { data } = await createResource(
  'devices',
  buildProjectDevicePayload(deviceBinding, {
    customerOrgId: overview.value?.customer?.id,
    salesPersonId: overview.value?.sales_person?.id,
  }),
)
```

- [ ] **Step 4: Replace the existing-device dropdown to use filtered candidates**

```vue
<el-option
  v-for="device in customerScopedDevices"
  :key="device.id"
  :label="formatDeviceOptionLabel(device, deviceModels)"
  :value="device.id"
/>
```

- [ ] **Step 5: Re-run the utility test and frontend build**

Run:

```powershell
cd frontend
node --test src/utils/projectDeviceForm.test.js
npm run build
```

Expected: both commands pass.

- [ ] **Step 6: Commit the customer-scoped device flow**

```bash
git add frontend/src/views/DeviceCenterView.vue frontend/src/utils/projectDeviceForm.js frontend/src/utils/projectDeviceForm.test.js
git commit -m "feat: scope project devices to the current customer"
```

### Task 6: Split project contracts from project attachments in the project center

**Files:**
- Modify: `frontend/src/api/resources.js`
- Modify: `frontend/src/views/DeviceCenterView.vue`

- [ ] **Step 1: Add API helpers for project contract binding**

```javascript
export function createProjectContract(payload) {
  return createResource('project-contracts', payload)
}

export function deleteProjectContract(id) {
  return deleteResource('project-contracts', id)
}
```

- [ ] **Step 2: Split the combined tab into separate contract and attachment tabs**

```vue
<el-tab-pane label="关联合同" name="contracts">
  <el-form inline>
    <el-form-item label="选择合同">
      <el-select v-model="selectedContractId" filterable clearable placeholder="选择该客户相关合同">
        <el-option
          v-for="contract in customerScopedContracts"
          :key="contract.id"
          :label="`${contract.contract_no} / ${contract.contract_name}`"
          :value="contract.id"
        />
      </el-select>
    </el-form-item>
    <el-button type="primary" @click="bindContract">关联合同</el-button>
  </el-form>

  <el-table :data="overview.contracts">
    <el-table-column prop="contract_no" label="合同编号" min-width="150" />
    <el-table-column prop="contract_name" label="合同名称" min-width="220" />
    <el-table-column prop="amount" label="金额" min-width="120" />
  </el-table>
</el-tab-pane>

<el-tab-pane label="项目附件" name="attachments">
  <!-- keep existing upload table here -->
</el-tab-pane>
```

- [ ] **Step 3: Add customer-scoped contract loading and bind action**

```javascript
const contracts = ref([])
const selectedContractId = ref(null)

const customerScopedContracts = computed(() =>
  contracts.value.filter((contract) => {
    if (!overview.value?.customer?.id) return true
    return contract.final_customer === overview.value.customer.id
  }),
)

async function loadOptions() {
  devices.value = unwrapList((await listResource('devices')).data)
  deviceModels.value = unwrapList((await listResource('device-models')).data)
  contracts.value = unwrapList((await listResource('contracts')).data)
  const people = unwrapList((await listResource('people')).data)
  salesPeople.value = people.filter((person) => person.person_type === 'sales')
  opsPeople.value = people.filter((person) => person.person_type === 'ops' || person.person_type === 'internal')
}

async function bindContract() {
  if (!activeProjectId.value || !selectedContractId.value) {
    ElMessage.warning('请选择要关联的合同')
    return
  }
  await createProjectContract({
    project: activeProjectId.value,
    contract: selectedContractId.value,
  })
  selectedContractId.value = null
  await openDetail({ id: activeProjectId.value })
}
```

- [ ] **Step 4: Build and manually verify the project drawer**

Run:

```powershell
cd frontend
npm run build
```

Expected: the project drawer now has four tabs, contracts can be linked independently, and attachments still upload as before.

- [ ] **Step 5: Commit the project-center tab split**

```bash
git add frontend/src/api/resources.js frontend/src/views/DeviceCenterView.vue
git commit -m "feat: separate project contracts from attachments"
```

### Task 7: Run the full verification sweep

**Files:**
- Modify: `docs/superpowers/specs/2026-07-03-project-customer-linking-design.md` (only if implementation diverged)
- Modify: `docs/superpowers/plans/2026-07-03-project-customer-linking.md` (only if implementation sequencing changes)

- [ ] **Step 1: Run the backend test suite**

Run:

```powershell
cd backend
python manage.py test
```

Expected: `OK` across existing and newly added tests.

- [ ] **Step 2: Run the frontend utility tests**

Run:

```powershell
cd frontend
node --test src/utils/*.test.js
```

Expected: all utility tests pass.

- [ ] **Step 3: Run the production build**

Run:

```powershell
cd frontend
npm run build
```

Expected: `vite build` completes successfully.

- [ ] **Step 4: Smoke-check the core user flow**

Manual verification checklist:

```text
1. 在项目中心创建一个项目并选择客户、联系人、销售。
2. 打开该项目详情，确认设备候选只显示该客户设备。
3. 新建设备后，确认设备回到客户中心的“已购设备”可见。
4. 绑定一个已有合同到项目。
5. 打开客户中心对应客户，确认“关联项目”tab能看到该项目。
6. 从客户中心打开项目详情，确认合同和附件分开显示。
```

- [ ] **Step 5: Commit the verified integration state**

```bash
git add backend frontend docs
git commit -m "feat: link customer and project center workflows"
```

## Self-Review

- Spec coverage:
  - 项目创建归属客户：Task 5
  - 客户中心展示项目：Task 3 and Task 4
  - 项目设备按客户过滤：Task 5
  - 项目关联合同：Task 2, Task 3, and Task 6
  - 合同和附件拆分：Task 6
- Placeholder scan:
  - No `TODO` or `TBD` placeholders remain
  - Each task contains file paths, code, and commands
- Type consistency:
  - `ProjectContract`, `project_contracts`, `customerScopedDevices`, `customerScopedContracts`, and `buildProjectDevicePayload` are used consistently across tasks
