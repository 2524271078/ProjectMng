# 客户设备 Tab 与设备中心搜索 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让客户中心“已购设备”Tab 与设备中心的设备列表和详情口径保持一致，并为设备中心补充真实搜索和更完整的工具区 UI。

**Architecture:** 后端只扩展现有 `/api/devices/` 列表查询能力，不新增接口；前端在 `DeviceDirectoryView.vue` 上增加真实搜索和更完整的工具区，并在 `CustomerCenterView.vue` 的“已购设备”Tab 内同步列表字段、详情字段和局部搜索。为控制范围，本轮不抽公共组件，不修改项目中心设备列表。

**Tech Stack:** Django REST Framework、Vue 3、Element Plus、Vite

---

## File Structure

- Modify: `backend/projects/views.py`
  - 为 `DeviceViewSet` 增加设备中心真实搜索逻辑
- Modify: `backend/projects/tests.py`
  - 为设备中心真实搜索补后端回归测试
- Modify: `frontend/src/views/DeviceDirectoryView.vue`
  - 增加搜索状态、搜索工具区、优化表格与详情弹窗字段
- Modify: `frontend/src/views/CustomerCenterView.vue`
  - 同步“已购设备”Tab 的表格字段、搜索栏和详情弹窗字段

### Task 1: 后端设备真实搜索

**Files:**
- Modify: `backend/projects/views.py`
- Modify: `backend/projects/tests.py`

- [ ] **Step 1: 写失败测试**

在 `backend/projects/tests.py` 末尾现有 `DeviceDirectoryApiTests` 后补一条搜索测试：

```python
    def test_device_list_search_matches_device_customer_contact_and_sales(self):
        customer = Organization.objects.create(name="搜索客户", org_type="customer")
        contact = Person.objects.create(name="搜索联系人", organization=customer, person_type="customer_contact")
        sales = Person.objects.create(name="搜索销售", person_type="sales")
        product = Product.objects.create(name="搜索产品", product_code="DEVICE-SEARCH-P")
        model = DeviceModel.objects.create(product=product, model_name="SEARCH-1000", model_code="SEARCH-1000")
        device = Device.objects.create(
            name="搜索设备",
            serial_number="SEARCH-SN-001",
            device_model=model,
            customer_org=customer,
            sales_person=sales,
        )
        project = Project.objects.create(
            project_no="DEVICE-SEARCH-PRJ-001",
            name="搜索项目",
            customer_org=customer,
            customer_contact=contact,
            sales_person=sales,
        )
        ProjectDevice.objects.create(
            project=project,
            device=device,
            service_type="new_install",
            service_start_date="2026-07-01",
            service_end_date="2027-06-30",
        )

        by_device = self.client.get("/api/devices/?search=搜索设备")
        by_serial = self.client.get("/api/devices/?search=SEARCH-SN-001")
        by_customer = self.client.get("/api/devices/?search=搜索客户")
        by_contact = self.client.get("/api/devices/?search=搜索联系人")
        by_sales = self.client.get("/api/devices/?search=搜索销售")

        for response in [by_device, by_serial, by_customer, by_contact, by_sales]:
            self.assertEqual(response.status_code, 200)
            self.assertEqual([item["id"] for item in response.data], [device.id])
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python manage.py test projects.tests.DeviceDirectoryApiTests
```

Expected:

```text
FAIL or ERROR because /api/devices/?search=搜索联系人 does not filter by the new fields yet
```

- [ ] **Step 3: 实现最小搜索逻辑**

在 `backend/projects/views.py` 中把 `DeviceViewSet` 从无自定义查询改成带搜索的查询集：

```python
class DeviceViewSet(SoftDeleteModelViewSet):
    queryset = Device.objects.select_related("device_model", "customer_org", "sales_person", "ops_person").prefetch_related(
        "project_devices__project__customer_org",
        "project_devices__project__customer_contact",
        "project_devices__project__sales_person",
    ).all()
    serializer_class = DeviceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search_value = self.request.query_params.get("search", "").strip()
        if not search_value:
            return queryset

        queryset = apply_search(queryset, search_value, ["name", "serial_number", "customer_org__name", "sales_person__name"])
        latest_contact_ids = Project.objects.filter(
            project_devices__device__in=queryset,
            customer_contact__name__icontains=search_value,
            project_devices__is_deleted=False,
            is_deleted=False,
        ).values_list("project_devices__device_id", flat=True)
        return queryset.filter(Q(id__in=latest_contact_ids) | Q(name__icontains=search_value) | Q(serial_number__icontains=search_value) | Q(customer_org__name__icontains=search_value) | Q(sales_person__name__icontains=search_value)).distinct()
```

实现时如果觉得重复条件太多，可以先组一个 `search_conditions = Q(...)`，但只保留本任务所需字段，不扩到型号编码、运维等无关字段。

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python manage.py test projects.tests.DeviceDirectoryApiTests
```

Expected:

```text
Ran 3 tests ... OK
```

- [ ] **Step 5: 运行完整后端测试**

Run:

```bash
python manage.py test
```

Expected:

```text
0 failures, 0 errors
```

- [ ] **Step 6: 提交后端模块**

```bash
git add backend/projects/views.py backend/projects/tests.py
git commit -m "feat: 增加设备中心真实搜索"
```

### Task 2: 设备中心搜索与工具区 UI

**Files:**
- Modify: `frontend/src/views/DeviceDirectoryView.vue`

- [ ] **Step 1: 在页面中增加搜索工具区**

把当前只有“刷新设备”的头部操作区调整为：

```vue
<div class="section-head">
  <div>
    <span class="eyebrow-dark">Device Center</span>
    <h2>设备中心</h2>
  </div>
  <div class="action-row">
    <el-input
      v-model="searchKeyword"
      placeholder="搜索设备 / 序列号 / 客户公司 / 联系人 / 销售"
      clearable
      @keyup.enter="handleSearch"
    />
    <el-button type="primary" @click="handleSearch">搜索</el-button>
    <el-button @click="resetSearch">重置</el-button>
    <el-button type="primary" plain @click="loadDevices">刷新设备</el-button>
  </div>
</div>
```

- [ ] **Step 2: 接入真实搜索状态与加载逻辑**

在 `script setup` 中加入：

```js
const searchKeyword = ref('')

async function loadDevices() {
  try {
    const params = searchKeyword.value.trim() ? { search: searchKeyword.value.trim() } : undefined
    const { data } = await listResource('devices', params)
    devices.value = unwrapList(data)
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载设备列表失败'))
  }
}

function handleSearch() {
  loadDevices()
}

function resetSearch() {
  searchKeyword.value = ''
  loadDevices()
}
```

- [ ] **Step 3: 同步详情字段**

在详情弹窗里保留现有字段，并确认包含：

```vue
<el-descriptions-item label="客户公司">{{ selectedDevice.customer?.name || selectedDevice.customer_org_detail?.name || '-' }}</el-descriptions-item>
<el-descriptions-item label="客户联系人">{{ selectedDevice.customer_contact?.name || selectedDevice.customer_contact_detail?.name || '-' }}</el-descriptions-item>
<el-descriptions-item label="销售">{{ selectedDevice.sales_person?.name || selectedDevice.sales_person_detail?.name || '-' }}</el-descriptions-item>
```

如果缺失“部署位置”，补回这一行，避免详情字段比客户中心少：

```vue
<el-descriptions-item label="部署位置">{{ selectedDevice.deploy_location || '-' }}</el-descriptions-item>
```

- [ ] **Step 4: 运行前端构建**

Run:

```bash
npm run build
```

Expected:

```text
vite build exits 0
```

- [ ] **Step 5: 提交设备中心前端模块**

```bash
git add frontend/src/views/DeviceDirectoryView.vue
git commit -m "feat: 完善设备中心搜索与展示"
```

### Task 3: 客户中心已购设备 Tab 同步

**Files:**
- Modify: `frontend/src/views/CustomerCenterView.vue`

- [ ] **Step 1: 为已购设备 Tab 增加局部搜索状态**

在 `script setup` 中新增：

```js
const deviceSearchKeyword = ref('')

const filteredCustomerDevices = computed(() => {
  const keyword = deviceSearchKeyword.value.trim()
  const devices = overview.value?.devices || []
  if (!keyword) return devices
  return devices.filter((device) => {
    const haystacks = [
      device.name,
      device.serial_number,
      device.customer_contact?.name,
      device.customer_contact_detail?.name,
      device.sales_person?.name,
      device.sales_person_detail?.name,
    ].filter(Boolean)
    return haystacks.some((value) => value.includes(keyword))
  })
})

function resetDeviceSearch() {
  deviceSearchKeyword.value = ''
}
```

- [ ] **Step 2: 替换已购设备 Tab 的表格头和数据源**

把旧的简单表格改成：

```vue
<el-tab-pane label="已购设备" name="devices">
  <div class="section-head compact mb-16">
    <span>设备列表</span>
    <div class="action-row">
      <el-input
        v-model="deviceSearchKeyword"
        placeholder="搜索设备 / 序列号 / 联系人 / 销售"
        clearable
        @keyup.enter="() => {}"
      />
      <el-button @click="resetDeviceSearch">重置</el-button>
    </div>
  </div>
  <el-table :data="filteredCustomerDevices">
    <el-table-column prop="name" label="设备" min-width="180" />
    <el-table-column prop="serial_number" label="序列号" min-width="160" />
    <el-table-column prop="current_service_status" label="当前保内状态" min-width="120" />
    <el-table-column prop="current_service_start_date" label="服务开始" min-width="140" />
    <el-table-column prop="current_service_end_date" label="服务结束" min-width="140" />
    <el-table-column label="客户公司" min-width="200">
      <template #default="scope">{{ scope.row.customer_org?.name || overview.customer.name || '-' }}</template>
    </el-table-column>
    <el-table-column label="客户联系人" min-width="160">
      <template #default="scope">{{ scope.row.customer_contact?.name || '-' }}</template>
    </el-table-column>
    <el-table-column label="销售" min-width="140">
      <template #default="scope">{{ scope.row.sales_person?.name || '-' }}</template>
    </el-table-column>
    <el-table-column label="操作" width="100">
      <template #default="scope">
        <el-button link type="primary" @click.stop="openDeviceDetail(scope.row)">详情</el-button>
      </template>
    </el-table-column>
  </el-table>
</el-tab-pane>
```

- [ ] **Step 3: 同步客户中心设备详情字段**

在客户中心现有 `deviceDetailVisible` 弹窗里补齐与设备中心一致的三行：

```vue
<el-descriptions-item label="客户公司">{{ selectedDevice.customer?.name || selected?.name || '-' }}</el-descriptions-item>
<el-descriptions-item label="客户联系人">{{ selectedDevice.customer_contact?.name || '-' }}</el-descriptions-item>
<el-descriptions-item label="销售">{{ selectedDevice.sales_person?.name || '-' }}</el-descriptions-item>
```

并保留原有的服务字段与授权、备注字段。

- [ ] **Step 4: 运行前端构建**

Run:

```bash
npm run build
```

Expected:

```text
vite build exits 0
```

- [ ] **Step 5: 提交客户中心模块**

```bash
git add frontend/src/views/CustomerCenterView.vue
git commit -m "feat: 同步客户中心设备展示"
```

## Self-Review

- Spec coverage:
  - 设备中心真实搜索：Task 1 + Task 2
  - 客户中心“已购设备”Tab 同步字段与详情：Task 3
  - 不改关联项目设备列表：本计划未触碰 `ProjectCenter` 相关设备列表文件
- Placeholder scan:
  - 无 `TODO/TBD`
  - 每个任务都有明确文件、命令和提交点
- Type consistency:
  - 设备中心搜索统一使用 `searchKeyword`
  - 客户中心 Tab 搜索统一使用 `deviceSearchKeyword`
  - 列表字段名称统一围绕 `customer_org_detail / customer_contact_detail / sales_person_detail`
