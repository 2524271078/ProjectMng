# 模块搜索 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为客户中心、项目中心、销售中心、产品中心增加统一的真实搜索能力，并确保搜索只覆盖各模块关键列表字段。

**Architecture:** 后端直接扩展现有列表接口，在 `get_queryset()` 中读取 `search` 查询参数并做限定字段的 `icontains` 过滤；前端在四个模块的列表区域增加统一的搜索栏，触发后端重查，不再依赖前端本地数组做主搜索。产品中心保留树结构，右侧型号列表搜索同时受树节点范围约束。

**Tech Stack:** Django REST Framework, Django ORM `Q` 查询, Vue 3 `script setup`, Element Plus, 现有 `listResource` API 包装。

---

## File Structure

**Backend**

- Modify: `backend/projects/views.py`
  - 为 `OrganizationViewSet` 增加客户搜索
  - 为 `PersonViewSet` 增加销售搜索
  - 为 `DeviceModelViewSet` 增加型号搜索和节点范围过滤
  - 为 `ProjectViewSet` 增加项目搜索
- Modify: `backend/projects/tests.py`
  - 增加四个模块的搜索接口测试

**Frontend**

- Modify: `frontend/src/views/CustomerCenterView.vue`
  - 增加客户搜索栏
  - `loadOrganizations()` 支持 `search`
- Modify: `frontend/src/views/DeviceCenterView.vue`
  - 增加项目搜索栏
  - `loadProjects()` 支持 `search`
- Modify: `frontend/src/views/SalesCenterView.vue`
  - 增加销售搜索栏
  - `loadSales()` 支持 `search`
- Modify: `frontend/src/views/ProductModelView.vue`
  - 增加型号搜索栏
  - `loadAll()` 中型号列表请求支持 `search` + 节点范围参数

---

### Task 1: 后端客户与销售搜索

**Files:**
- Modify: `backend/projects/views.py`
- Test: `backend/projects/tests.py`

- [ ] **Step 1: Write the failing test**

```python
class SearchApiTests(APITestCase):
    def test_organization_list_supports_search_by_name_region_and_type(self):
        customer = Organization.objects.create(name="国网华东", org_type="customer", region="华东")
        Organization.objects.create(name="南网广州", org_type="customer", region="华南")

        response = self.client.get("/api/organizations/?search=华东")

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertIn(customer.name, names)
        self.assertNotIn("南网广州", names)

    def test_sales_list_supports_search_by_name_phone_and_email(self):
        sales = Person.objects.create(name="许超飞", person_type="sales", phone="13800000001", email="xu@example.com")
        Person.objects.create(name="测试联系人", person_type="customer_contact", phone="13800000002", email="contact@example.com")

        response = self.client.get("/api/people/?person_type=sales&search=许超")

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertIn(sales.name, names)
        self.assertNotIn("测试联系人", names)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd backend
..\.venv\Scripts\python.exe manage.py test projects.tests.SearchApiTests.test_organization_list_supports_search_by_name_region_and_type projects.tests.SearchApiTests.test_sales_list_supports_search_by_name_phone_and_email
```

Expected: FAIL，因为当前 `OrganizationViewSet` / `PersonViewSet` 还没有读取 `search` 参数做过滤。

- [ ] **Step 3: Write minimal implementation**

在 `backend/projects/views.py` 中为 `OrganizationViewSet` 和 `PersonViewSet` 重写 `get_queryset()`，示例结构：

```python
from django.db.models import Q

class OrganizationViewSet(SoftDeleteModelViewSet):
    queryset = Organization.objects.all().order_by("id")
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(region__icontains=search)
                | Q(org_type__icontains=search)
            )
        return queryset

class PersonViewSet(SoftDeleteModelViewSet):
    queryset = Person.objects.select_related("organization").all().order_by("id")
    serializer_class = PersonSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        person_type = self.request.query_params.get("person_type")
        if person_type:
            queryset = queryset.filter(person_type=person_type)
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
            )
        return queryset
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd backend
..\.venv\Scripts\python.exe manage.py test projects.tests.SearchApiTests.test_organization_list_supports_search_by_name_region_and_type projects.tests.SearchApiTests.test_sales_list_supports_search_by_name_phone_and_email
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/projects/views.py backend/projects/tests.py
git commit -m "feat: 增加客户与销售真实搜索"
```

### Task 2: 后端项目与产品型号搜索

**Files:**
- Modify: `backend/projects/views.py`
- Test: `backend/projects/tests.py`

- [ ] **Step 1: Write the failing test**

```python
class SearchApiTests(APITestCase):
    def test_project_list_supports_search_by_project_customer_sales_and_stage(self):
        customer = Organization.objects.create(name="国网电力公司", org_type="customer")
        sales = Person.objects.create(name="许超飞", person_type="sales")
        Project.objects.create(project_no="P-001", name="华东交付项目", customer_org=customer, sales_person=sales, project_stage="delivery")
        Project.objects.create(project_no="P-002", name="西北巡检项目", project_stage="ops")

        response = self.client.get("/api/projects/?search=国网")

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertIn("华东交付项目", names)
        self.assertNotIn("西北巡检项目", names)

    def test_device_model_list_supports_search_by_model_product_and_version(self):
        product = Product.objects.create(name="边界防护", product_code="EDGE-P")
        version = ProductVersion.objects.create(product=product, version_name="V5.0", version_code="5.0")
        matched = DeviceModel.objects.create(product=product, product_version=version, model_name="SG-3000", model_code="SG3000")
        DeviceModel.objects.create(product=product, model_name="SG-1000", model_code="SG1000")

        response = self.client.get("/api/device-models/?search=SG3000")

        self.assertEqual(response.status_code, 200)
        codes = [item["model_code"] for item in response.data]
        self.assertIn(matched.model_code, codes)
        self.assertNotIn("SG1000", codes)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd backend
..\.venv\Scripts\python.exe manage.py test projects.tests.SearchApiTests.test_project_list_supports_search_by_project_customer_sales_and_stage projects.tests.SearchApiTests.test_device_model_list_supports_search_by_model_product_and_version
```

Expected: FAIL，因为当前 `ProjectViewSet` 和 `DeviceModelViewSet` 尚未处理 `search`。

- [ ] **Step 3: Write minimal implementation**

在 `backend/projects/views.py` 中补充：

```python
class ProjectViewSet(SoftDeleteModelViewSet):
    queryset = Project.objects.select_related("customer_org", "customer_contact", "sales_person", "ops_person").all().order_by("id")
    serializer_class = ProjectSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(customer_org__name__icontains=search)
                | Q(sales_person__name__icontains=search)
                | Q(project_stage__icontains=search)
            ).distinct()
        return queryset

class DeviceModelViewSet(SoftDeleteModelViewSet):
    queryset = DeviceModel.objects.select_related("product", "product_version", "manufacturer").all().order_by("id")
    serializer_class = DeviceModelSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        line_id = self.request.query_params.get("product_line")
        product_id = self.request.query_params.get("product")
        version_id = self.request.query_params.get("product_version")
        if version_id:
            queryset = queryset.filter(product_version_id=version_id)
        elif product_id:
            queryset = queryset.filter(product_id=product_id)
        elif line_id:
            queryset = queryset.filter(product__product_line_id=line_id)
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(model_name__icontains=search)
                | Q(model_code__icontains=search)
                | Q(product__name__icontains=search)
                | Q(product_version__version_name__icontains=search)
            ).distinct()
        return queryset
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd backend
..\.venv\Scripts\python.exe manage.py test projects.tests.SearchApiTests.test_project_list_supports_search_by_project_customer_sales_and_stage projects.tests.SearchApiTests.test_device_model_list_supports_search_by_model_product_and_version
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/projects/views.py backend/projects/tests.py
git commit -m "feat: 增加项目与型号真实搜索"
```

### Task 3: 前端客户、项目、销售搜索栏

**Files:**
- Modify: `frontend/src/views/CustomerCenterView.vue`
- Modify: `frontend/src/views/DeviceCenterView.vue`
- Modify: `frontend/src/views/SalesCenterView.vue`

- [ ] **Step 1: Write the failing test**

本仓库当前没有稳定的前端组件测试框架，本任务使用可复现的手工失败标准代替自动化 UI 测试：

- 客户中心顶部没有搜索框
- 项目中心顶部没有搜索框
- 销售中心顶部没有搜索框
- 对 `listResource` 的调用没有带 `search` 参数

先通过代码检视确认这三个页面不存在 `searchKeyword`、搜索按钮和重置按钮。

- [ ] **Step 2: Run check to verify current state is missing the feature**

Run:
```bash
rg -n "searchKeyword|搜索|重置|listResource\('organizations'|listResource\('projects'|listResource\('people'" frontend/src/views/CustomerCenterView.vue frontend/src/views/DeviceCenterView.vue frontend/src/views/SalesCenterView.vue
```

Expected: 没有这套统一搜索实现，或只有无关文本。

- [ ] **Step 3: Write minimal implementation**

为三个页面分别增加：

```vue
<el-input v-model="searchKeyword" placeholder="搜索..." clearable @keyup.enter="handleSearch" />
<el-button @click="handleSearch">搜索</el-button>
<el-button @click="resetSearch">重置</el-button>
```

并增加对应状态和加载逻辑：

```js
const searchKeyword = ref('')

async function loadProjects() {
  const params = searchKeyword.value.trim() ? { search: searchKeyword.value.trim() } : {}
  const { data } = await listResource('projects', params)
  projects.value = unwrapList(data)
}

function handleSearch() {
  loadProjects()
}

function resetSearch() {
  searchKeyword.value = ''
  loadProjects()
}
```

客户中心使用 `organizations`，销售中心使用 `people`，并保留 `person_type: 'sales'`。

- [ ] **Step 4: Run build to verify it passes**

Run:
```bash
cd frontend
cmd /c npm run build
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/CustomerCenterView.vue frontend/src/views/DeviceCenterView.vue frontend/src/views/SalesCenterView.vue
git commit -m "feat: 增加客户项目销售搜索栏"
```

### Task 4: 前端产品中心真实搜索

**Files:**
- Modify: `frontend/src/views/ProductModelView.vue`

- [ ] **Step 1: Write the failing test**

本任务同样使用可复现的手工失败标准：

- 产品中心右侧没有搜索栏
- `loadAll()` 中 `device-models` 请求没有带树节点约束参数和 `search` 参数

- [ ] **Step 2: Run check to verify current state is missing the feature**

Run:
```bash
rg -n "searchKeyword|device-models|product_line|product_version|搜索|重置" frontend/src/views/ProductModelView.vue
```

Expected: 缺少统一搜索栏和“节点范围 + search”联合请求。

- [ ] **Step 3: Write minimal implementation**

在右侧型号列表区域增加搜索栏，并将 `loadAll()` 拆成：

```js
const searchKeyword = ref('')

function currentModelFilters() {
  const params = {}
  if (selectedNode.value?.type === 'line') params.product_line = selectedNode.value.id
  if (selectedNode.value?.type === 'product') params.product = selectedNode.value.id
  if (selectedNode.value?.type === 'version') params.product_version = selectedNode.value.id
  if (searchKeyword.value.trim()) params.search = searchKeyword.value.trim()
  return params
}

async function loadModels() {
  models.value = unwrapList((await listResource('device-models', currentModelFilters())).data)
}
```

并在以下时机触发 `loadModels()`：

- 页面初始化
- 搜索
- 重置
- 树节点切换
- 型号新增/编辑/删除后刷新

`loadAll()` 只保留树相关三组基础数据加载，再单独调用 `loadModels()`。

- [ ] **Step 4: Run build to verify it passes**

Run:
```bash
cd frontend
cmd /c npm run build
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/ProductModelView.vue
git commit -m "feat: 增加产品中心真实搜索"
```

### Task 5: 全量回归验证

**Files:**
- Modify: `backend/projects/tests.py` (if final cleanup needed)
- Modify: `frontend/src/views/*.vue` (only if verification暴露问题)

- [ ] **Step 1: Run backend full test suite**

Run:
```bash
cd backend
..\.venv\Scripts\python.exe manage.py test
```

Expected: PASS

- [ ] **Step 2: Run frontend production build**

Run:
```bash
cd frontend
cmd /c npm run build
```

Expected: PASS

- [ ] **Step 3: Final diff review**

Run:
```bash
git diff --stat
```

Expected: 仅包含本次搜索相关后端视图、测试、前端页面改动。

- [ ] **Step 4: Commit final verification adjustments if needed**

```bash
git add <verified-files>
git commit -m "fix: 收口模块搜索联调细节"
```

仅当回归阶段为修正联调问题产生了新改动时执行；若无新改动，则跳过此提交。
