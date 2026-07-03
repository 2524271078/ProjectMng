# 全系统表格统一分页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为客户中心、项目中心、设备中心、销售中心、产品型号等表格型列表统一接入真实分页查询，并保持搜索、筛选、详情抽屉列表的一致交互。

**Architecture:** 后端先在 `backend/projects/views.py` 上建立统一分页能力，并为 overview 内的重列表拆出独立分页接口；前端再以 `frontend/src/api/resources.js` 为统一入口，在各视图页分别接入 `page/page_size/count/results` 协议。改造遵循分模块提交，先打底层协议，再逐页替换。

**Tech Stack:** Django REST Framework、Vue 3、Element Plus、Vite

---

## File Structure

**Backend core**
- Modify: `backend/projects/views.py`
  - 统一列表分页
  - 新增客户/项目详情子表格分页接口
- Modify: `backend/projects/tests.py`
  - 分页协议测试
  - 详情子列表分页测试

**Frontend shared**
- Modify: `frontend/src/api/resources.js`
  - 增加详情子表格分页接口访问方法
- Create: `frontend/src/utils/pagination.js`
  - 统一分页状态与响应解析辅助函数

**Frontend pages**
- Modify: `frontend/src/views/DeviceCenterView.vue`
  - 项目中心主列表分页
  - 项目详情 tab 子表格分页
- Modify: `frontend/src/views/CustomerCenterView.vue`
  - 客户 tab 子表格分页
- Modify: `frontend/src/views/DeviceDirectoryView.vue`
  - 设备中心主列表分页
- Modify: `frontend/src/views/SalesCenterView.vue`
  - 销售中心主列表分页
- Modify: `frontend/src/views/ProductModelView.vue`
  - 产品型号列表分页
- Modify: `frontend/src/views/PersonManageView.vue`
  - 人员管理主列表分页（销售人员列表依赖）

---

### Task 1: 后端统一列表分页基础能力

**Files:**
- Modify: `backend/projects/views.py`
- Test: `backend/projects/tests.py`

- [ ] **Step 1: 写后端分页失败测试**

```python
class PaginationApiTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="pagination-api", password="pass123456")
        self.client.force_authenticate(self.user)

    def test_people_list_returns_default_pagination_shape(self):
        for index in range(12):
            Person.objects.create(name=f"销售{index}", person_type="sales")

        response = self.client.get("/api/people/?person_type=sales")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 10)
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(response.data["total_pages"], 2)
        self.assertEqual(len(response.data["results"]), 10)
```

- [ ] **Step 2: 运行失败测试，确认当前接口仍是非统一分页结构**

Run: `python manage.py test projects.tests.PaginationApiTests.test_people_list_returns_default_pagination_shape`
Expected: `FAIL`，报错点应落在 `response.data["page"]` 或响应结构不是字典。

- [ ] **Step 3: 在 `views.py` 增加统一分页辅助函数并接入主列表 ViewSet**

```python
from math import ceil
from rest_framework.response import Response


def paginate_queryset(request, queryset, default_page_size=10):
    page = parse_query_int(request.query_params.get("page")) or 1
    page_size = parse_query_int(request.query_params.get("page_size")) or default_page_size
    page = max(page, 1)
    page_size = max(page_size, 1)
    page_size = min(page_size, 100)

    count = queryset.count()
    total_pages = max(ceil(count / page_size), 1) if count else 1
    start = (page - 1) * page_size
    end = start + page_size
    return queryset[start:end], {
        "count": count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


class SoftDeleteModelViewSet(viewsets.ModelViewSet):
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page_items, meta = paginate_queryset(request, queryset)
        serializer = self.get_serializer(page_items, many=True)
        return Response({**meta, "results": serializer.data})
```

- [ ] **Step 4: 增加非法分页参数与搜索叠加测试**

```python
def test_people_list_supports_search_and_safe_invalid_page_size(self):
    Person.objects.create(name="许超飞", person_type="sales")
    Person.objects.create(name="李四", person_type="sales")

    response = self.client.get("/api/people/?person_type=sales&search=许超飞&page=abc&page_size=xyz")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data["page"], 1)
    self.assertEqual(response.data["page_size"], 10)
    self.assertEqual(response.data["count"], 1)
    self.assertEqual([item["name"] for item in response.data["results"]], ["许超飞"])
```

- [ ] **Step 5: 运行后端分页定向测试**

Run: `python manage.py test projects.tests.PaginationApiTests -v 2`
Expected: `OK`

- [ ] **Step 6: 运行后端全量测试**

Run: `python manage.py test`
Expected: `OK`

- [ ] **Step 7: 提交**

```bash
git add backend/projects/views.py backend/projects/tests.py
git commit -m "feat: 增加统一分页基础能力"
```

### Task 2: 后端拆分客户与项目详情子表格分页接口

**Files:**
- Modify: `backend/projects/views.py`
- Test: `backend/projects/tests.py`

- [ ] **Step 1: 写客户与项目详情子表格分页失败测试**

```python
def test_customer_devices_endpoint_returns_paginated_results(self):
    customer = Organization.objects.create(name="分页客户", org_type="customer")
    product = Product.objects.create(name="分页产品", product_code="PAGE-PRODUCT")
    model = DeviceModel.objects.create(product=product, model_name="PAGE-1000", model_code="PAGE-1000")
    project = Project.objects.create(project_no="PAGE-PRJ-001", name="分页项目", customer_org=customer)
    for index in range(12):
        device = Device.objects.create(name=f"设备{index}", serial_number=f"PAGE-SN-{index}", device_model=model)
        ProjectDevice.objects.create(project=project, device=device, service_type="renewal")

    response = self.client.get(f"/api/customers/{customer.id}/devices/?page=2&page_size=10")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data["page"], 2)
    self.assertEqual(len(response.data["results"]), 2)
```

```python
def test_project_devices_endpoint_returns_paginated_results(self):
    customer = Organization.objects.create(name="分页项目客户", org_type="customer")
    project = Project.objects.create(project_no="PAGE-PRJ-002", name="分页项目二", customer_org=customer)
    product = Product.objects.create(name="分页项目产品", product_code="PAGE-PROJECT-PRODUCT")
    model = DeviceModel.objects.create(product=product, model_name="PAGE-2000", model_code="PAGE-2000")
    for index in range(11):
        device = Device.objects.create(name=f"项目设备{index}", serial_number=f"PRJ-SN-{index}", device_model=model)
        ProjectDevice.objects.create(project=project, device=device, service_type="new_install")

    response = self.client.get(f"/api/projects/{project.id}/devices/?page=2&page_size=10")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data["count"], 11)
    self.assertEqual(len(response.data["results"]), 1)
```

- [ ] **Step 2: 运行上述测试，确认接口尚不存在或响应不符合预期**

Run: `python manage.py test projects.tests.CustomerPurchasedDeviceTests projects.tests.ProjectDetailPaginationTests -v 2`
Expected: `FAIL`，通常为 `404` 或响应结构不匹配。

- [ ] **Step 3: 在 `views.py` 增加详情子表格分页端点**

```python
@api_view(["GET"])
def customer_devices_list(request, pk):
    customer = Organization.objects.get(pk=pk)
    queryset = Device.objects.filter(
        project_devices__project__customer_org=customer,
        project_devices__is_deleted=False,
        is_deleted=False,
    ).distinct().order_by("id")
    page_items, meta = paginate_queryset(request, queryset)
    return Response({**meta, "results": DeviceSerializer(page_items, many=True).data})


@api_view(["GET"])
def project_devices_list(request, pk):
    queryset = ProjectDevice.objects.filter(project_id=pk, is_deleted=False).select_related("device", "device__device_model").order_by("id")
    page_items, meta = paginate_queryset(request, queryset)
    return Response({**meta, "results": [project_device_summary(item) for item in page_items]})
```

- [ ] **Step 4: 为客户联系人、销售、合同、附件列表补齐同类分页端点**

```python
@api_view(["GET"])
def customer_projects_list(request, pk):
    queryset = Project.objects.filter(customer_org_id=pk, is_deleted=False).select_related("customer_contact", "sales_person").order_by("id")
    page_items, meta = paginate_queryset(request, queryset)
    return Response({**meta, "results": [project_summary(item) for item in page_items]})
```

```python
@api_view(["GET"])
def project_contracts_list(request, pk):
    queryset = ProjectContract.objects.filter(project_id=pk, is_deleted=False).select_related("contract").order_by("id")
    page_items, meta = paginate_queryset(request, queryset)
    return Response({**meta, "results": [contract_summary(item.contract) for item in page_items]})
```

- [ ] **Step 5: 运行子表格分页定向测试**

Run: `python manage.py test projects.tests.CustomerPurchasedDeviceTests projects.tests.ProjectDetailPaginationTests -v 2`
Expected: `OK`

- [ ] **Step 6: 运行后端全量测试**

Run: `python manage.py test`
Expected: `OK`

- [ ] **Step 7: 提交**

```bash
git add backend/projects/views.py backend/projects/tests.py
git commit -m "feat: 拆分详情子列表分页接口"
```

### Task 3: 前端共享分页工具与 API 封装

**Files:**
- Modify: `frontend/src/api/resources.js`
- Create: `frontend/src/utils/pagination.js`

- [ ] **Step 1: 先写分页工具用例草案，明确返回结构读取方式**

```javascript
import { buildPaginationState, applyPaginationResponse } from '../utils/pagination'

const state = buildPaginationState()
applyPaginationResponse(state, {
  count: 21,
  page: 2,
  page_size: 10,
  total_pages: 3,
  results: [{ id: 11 }],
})

console.assert(state.page === 2)
console.assert(state.pageSize === 10)
console.assert(state.total === 21)
console.assert(state.rows.length === 1)
```

- [ ] **Step 2: 创建 `frontend/src/utils/pagination.js`**

```javascript
import { reactive } from 'vue'

export function buildPaginationState() {
  return reactive({
    page: 1,
    pageSize: 10,
    total: 0,
    totalPages: 1,
    rows: [],
    loading: false,
  })
}

export function applyPaginationResponse(state, payload) {
  state.page = payload.page || 1
  state.pageSize = payload.page_size || 10
  state.total = payload.count || 0
  state.totalPages = payload.total_pages || 1
  state.rows = payload.results || []
}
```

- [ ] **Step 3: 在 `resources.js` 增加详情子表格 API 方法**

```javascript
export function fetchCustomerDevices(id, params = {}) {
  return apiClient.get(`/customers/${id}/devices/`, { params })
}

export function fetchCustomerProjects(id, params = {}) {
  return apiClient.get(`/customers/${id}/projects/`, { params })
}

export function fetchProjectDevices(id, params = {}) {
  return apiClient.get(`/projects/${id}/devices/`, { params })
}

export function fetchProjectContracts(id, params = {}) {
  return apiClient.get(`/projects/${id}/contracts/`, { params })
}
```

- [ ] **Step 4: 运行前端语法检查与构建**

Run: `npm run build`
Expected: `built in ...` 且退出码为 `0`

- [ ] **Step 5: 提交**

```bash
git add frontend/src/api/resources.js frontend/src/utils/pagination.js
git commit -m "feat: 增加前端分页工具与接口封装"
```

### Task 4: 项目中心分页接入

**Files:**
- Modify: `frontend/src/views/DeviceCenterView.vue`
- Verify: `backend/projects/views.py`

- [ ] **Step 1: 项目中心主列表先切到分页状态管理**

```javascript
import { buildPaginationState, applyPaginationResponse } from '../utils/pagination'

const projectPagination = buildPaginationState()

async function loadProjects() {
  projectPagination.loading = true
  try {
    const params = {
      page: projectPagination.page,
      page_size: projectPagination.pageSize,
      ...(searchKeyword.value.trim() ? { search: searchKeyword.value.trim() } : {}),
    }
    const { data } = await listResource('projects', params)
    applyPaginationResponse(projectPagination, data)
  } finally {
    projectPagination.loading = false
  }
}
```

- [ ] **Step 2: 搜索与页码联动**

```javascript
function handleSearch() {
  projectPagination.page = 1
  loadProjects()
}

function handleProjectPageChange(page) {
  projectPagination.page = page
  loadProjects()
}

function handleProjectPageSizeChange(pageSize) {
  projectPagination.page = 1
  projectPagination.pageSize = pageSize
  loadProjects()
}
```

- [ ] **Step 3: 项目详情 `设备 / 合同 / 附件` tab 改成独立分页加载**

```javascript
const projectDevicePagination = buildPaginationState()
const projectContractPagination = buildPaginationState()
const projectAttachmentPagination = buildPaginationState()

async function loadProjectDevices(projectId) {
  const { data } = await fetchProjectDevices(projectId, {
    page: projectDevicePagination.page,
    page_size: projectDevicePagination.pageSize,
  })
  applyPaginationResponse(projectDevicePagination, data)
}
```

- [ ] **Step 4: 在表格底部接入 Element Plus 分页组件**

```vue
<el-pagination
  background
  layout="total, sizes, prev, pager, next"
  :current-page="projectPagination.page"
  :page-size="projectPagination.pageSize"
  :page-sizes="[10, 20, 50]"
  :total="projectPagination.total"
  @current-change="handleProjectPageChange"
  @size-change="handleProjectPageSizeChange"
/>
```

- [ ] **Step 5: 前端构建验证**

Run: `npm run build`
Expected: `built in ...` 且退出码为 `0`

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/DeviceCenterView.vue
git commit -m "feat: 为项目中心接入分页查询"
```

### Task 5: 客户中心分页接入

**Files:**
- Modify: `frontend/src/views/CustomerCenterView.vue`
- Modify: `frontend/src/api/resources.js`

- [ ] **Step 1: 为每个 tab 建立独立分页状态**

```javascript
const contactPagination = buildPaginationState()
const salesPagination = buildPaginationState()
const devicePagination = buildPaginationState()
const contractPagination = buildPaginationState()
const projectPagination = buildPaginationState()
```

- [ ] **Step 2: 切换客户节点后统一重置页码**

```javascript
function resetCustomerTabPagination() {
  ;[contactPagination, salesPagination, devicePagination, contractPagination, projectPagination].forEach((state) => {
    state.page = 1
    state.pageSize = 10
    state.total = 0
    state.rows = []
  })
}
```

- [ ] **Step 3: 将 `已购设备 / 关联项目 / 关联合同` 改为独立分页请求**

```javascript
async function loadCustomerDevices(customerId) {
  const { data } = await fetchCustomerDevices(customerId, {
    page: devicePagination.page,
    page_size: devicePagination.pageSize,
    ...(deviceSearchKeyword.value.trim() ? { search: deviceSearchKeyword.value.trim() } : {}),
  })
  applyPaginationResponse(devicePagination, data)
}
```

- [ ] **Step 4: 联系人与负责销售如果暂未拆独立接口，则先在 overview 返回中分页化；若已拆接口，则统一改独立接口**

```javascript
<el-table :data="devicePagination.rows" stripe />
<el-pagination
  background
  layout="total, sizes, prev, pager, next"
  :current-page="devicePagination.page"
  :page-size="devicePagination.pageSize"
  :page-sizes="[10, 20, 50]"
  :total="devicePagination.total"
  @current-change="(page) => { devicePagination.page = page; loadCustomerDevices(selected.id) }"
  @size-change="(size) => { devicePagination.page = 1; devicePagination.pageSize = size; loadCustomerDevices(selected.id) }"
/>
```

- [ ] **Step 5: 前端构建验证**

Run: `npm run build`
Expected: `built in ...` 且退出码为 `0`

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/CustomerCenterView.vue frontend/src/api/resources.js
git commit -m "feat: 为客户中心接入分页查询"
```

### Task 6: 设备中心、销售中心、产品型号分页接入

**Files:**
- Modify: `frontend/src/views/DeviceDirectoryView.vue`
- Modify: `frontend/src/views/SalesCenterView.vue`
- Modify: `frontend/src/views/ProductModelView.vue`
- Modify: `frontend/src/views/PersonManageView.vue`

- [ ] **Step 1: 设备中心主列表接入分页参数与分页组件**

```javascript
const devicePagination = buildPaginationState()

async function loadDevices() {
  const { data } = await listResource('devices', {
    page: devicePagination.page,
    page_size: devicePagination.pageSize,
    ...(searchKeyword.value.trim() ? { search: searchKeyword.value.trim() } : {}),
  })
  applyPaginationResponse(devicePagination, data)
}
```

- [ ] **Step 2: 销售中心主列表分页，保留 `person_type=sales` 过滤**

```javascript
async function loadSales() {
  const params = {
    person_type: 'sales',
    page: salesPagination.page,
    page_size: salesPagination.pageSize,
    ...(searchKeyword.value.trim() ? { search: searchKeyword.value.trim() } : {}),
  }
  const { data } = await listResource('people', params)
  applyPaginationResponse(salesPagination, data)
}
```

- [ ] **Step 3: 产品型号主列表分页，树过滤与搜索切换时重置第一页**

```javascript
async function loadModels() {
  const params = {
    ...currentModelFilters(),
    page: modelPagination.page,
    page_size: modelPagination.pageSize,
  }
  const { data } = await listResource('device-models', params)
  applyPaginationResponse(modelPagination, data)
}
```

- [ ] **Step 4: 人员管理列表分页，确保销售客户关系编辑弹窗不受影响**

```javascript
async function loadPeople() {
  const { data } = await listResource('people', {
    page: peoplePagination.page,
    page_size: peoplePagination.pageSize,
  })
  applyPaginationResponse(peoplePagination, data)
}
```

- [ ] **Step 5: 前端构建验证**

Run: `npm run build`
Expected: `built in ...` 且退出码为 `0`

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/DeviceDirectoryView.vue frontend/src/views/SalesCenterView.vue frontend/src/views/ProductModelView.vue frontend/src/views/PersonManageView.vue
git commit -m "feat: 为列表模块接入统一分页"
```

### Task 7: 回归验证与收尾

**Files:**
- Verify only: `backend/projects/tests.py`
- Verify only: `frontend/src/views/*.vue`

- [ ] **Step 1: 后端全量回归**

Run: `python manage.py test`
Expected: `OK`

- [ ] **Step 2: 前端全量构建回归**

Run: `npm run build`
Expected: `built in ...` 且退出码为 `0`

- [ ] **Step 3: 手工走查关键链路**

```text
1. 项目中心搜索 -> 翻页 -> 打开项目详情 -> 切换设备/合同 tab
2. 客户中心切客户 -> 已购设备翻页 -> 搜索 -> 查看详情
3. 设备中心搜索 -> 保内/保外筛选 -> 翻页
4. 销售中心搜索 -> 翻页
5. 产品型号切树节点 -> 翻页 -> 搜索
```

- [ ] **Step 4: 输出剩余风险说明**

```text
- 若 overview 接口中仍保留全量子列表字段，需要确认前端已不再依赖它们作为分页数据源。
- 若未来补合同中心和系统管理分页，应复用同一协议与分页工具，不再另起实现。
```

## Self-Review

### Spec coverage
- 统一分页协议：Task 1
- 详情子表格独立分页接口：Task 2
- 前端统一分页工具：Task 3
- 项目中心分页：Task 4
- 客户中心分页：Task 5
- 设备/销售/产品模块分页：Task 6
- 构建与测试验证：Task 1/2/6/7

### Placeholder scan
- 已避免使用 `TODO`、`TBD`、`后续补齐` 这类占位描述。
- 每个任务都给出具体文件、命令和关键代码片段。

### Type consistency
- 统一使用 `page`、`page_size`、`count`、`results`、`total_pages`。
- 前端统一使用 `buildPaginationState` 和 `applyPaginationResponse`。
