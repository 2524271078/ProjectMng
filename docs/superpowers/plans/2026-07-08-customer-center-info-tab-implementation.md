# Customer Center Info Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将客户中心的 `客户详情`、`联系人`、`负责销售` 合并为一个 `客户信息` 页签，并保持设备、合同、项目页签和现有分页逻辑可用。

**Architecture:** 继续在 `frontend/src/views/CustomerCenterView.vue` 内完成结构调整，不引入新的后端接口。外层 tab 从 6 个收敛为 4 个；`客户信息` tab 内新增 3 个纵向区块，分别承载客户概览、联系人列表和销售列表；联系人和销售的加载入口从旧的独立 tab 触发改为客户切换时预加载。

**Tech Stack:** Vue 3 `script setup`、Element Plus、现有 `resources` API 封装、Vite。

---

### Task 1: 调整客户中心数据加载入口

**Files:**
- Modify: `frontend/src/views/CustomerCenterView.vue`
- Test: `frontend` build via `npm run build`

- [ ] **Step 1: 先定位并修改活动页签默认值与客户切换入口**

将以下状态与客户选择逻辑从旧页签名 `base` 切换到新页签名 `info`：

```js
const activeCustomerTab = ref('info')
```

```js
async function selectCustomer(node) {
  selected.value = node
  activeCustomerTab.value = 'info'
  deviceSearchKeyword.value = ''
  resetCustomerTabPagination()
  const { data } = await fetchCustomerOverview(node.id)
  overview.value = data
}
```

并同步检查文件底部其他将 `activeCustomerTab` 重置为 `base` 的地方，一并改为 `info`。

- [ ] **Step 2: 重写活动页签加载分发逻辑**

将旧的 `contacts`、`sales` 分发分支收敛到新的 `info` 页签，只保留设备、合同、项目的按需加载：

```js
async function loadCustomerInfoTab() {
  await Promise.all([
    loadCustomerContactsTab(),
    loadCustomerSalesTab(),
  ])
}

async function loadActiveCustomerTab() {
  if (activeCustomerTab.value === 'info') return loadCustomerInfoTab()
  if (activeCustomerTab.value === 'devices') return loadCustomerDevicesTab()
  if (activeCustomerTab.value === 'contracts') return loadCustomerContractsTab()
  if (activeCustomerTab.value === 'projects') return loadCustomerProjectsTab()
}
```

- [ ] **Step 3: 在客户选择后补上联系人与销售预加载**

在 `selectCustomer` 中获取 `overview` 后，立即加载 `客户信息` 页签所需的联系人与销售分页，避免新布局首屏出现空区块：

```js
async function selectCustomer(node) {
  selected.value = node
  activeCustomerTab.value = 'info'
  deviceSearchKeyword.value = ''
  resetCustomerTabPagination()
  const { data } = await fetchCustomerOverview(node.id)
  overview.value = data
  await loadCustomerInfoTab()
}
```

- [ ] **Step 4: 运行前端构建验证数据加载逻辑未引入语法错误**

Run: `npm run build`
Expected: `vite build` 退出码 0。

- [ ] **Step 5: 提交 Task 1**

```bash
git add frontend/src/views/CustomerCenterView.vue
git commit -m "feat: 调整客户中心信息页签加载逻辑"
```

### Task 2: 合并外层页签并迁移内容到客户信息区块

**Files:**
- Modify: `frontend/src/views/CustomerCenterView.vue`
- Test: `frontend` build via `npm run build`

- [ ] **Step 1: 将外层 tab 从 6 个改为 4 个**

把这 3 个旧页签：

```vue
<el-tab-pane label="客户详情" name="base">...</el-tab-pane>
<el-tab-pane label="联系人" name="contacts">...</el-tab-pane>
<el-tab-pane label="负责销售" name="sales">...</el-tab-pane>
```

替换成一个新页签：

```vue
<el-tab-pane label="客户信息" name="info">
  <!-- 客户详情区块 -->
  <!-- 联系人区块 -->
  <!-- 负责销售区块 -->
</el-tab-pane>
```

保留 `设备`、`合同`、`项目` 3 个页签不动。

- [ ] **Step 2: 在 `客户信息` 页签中迁移客户详情内容**

保留当前概览描述组件结构，放在第一个区块：

```vue
<section class="customer-info-section">
  <div class="customer-info-section__head">
    <h3>客户详情</h3>
  </div>
  <el-descriptions :column="2" border>
    <el-descriptions-item label="名称">{{ overview.customer.name }}</el-descriptions-item>
    <el-descriptions-item label="类型">{{ overview.customer.org_type }}</el-descriptions-item>
    <el-descriptions-item label="区域">{{ overview.customer.region || '-' }}</el-descriptions-item>
  </el-descriptions>
</section>
```

- [ ] **Step 3: 在 `客户信息` 页签中迁移联系人与销售表格**

将联系人页签内容迁入第二个区块，将销售页签内容迁入第三个区块，保留现有表格列和分页方法：

```vue
<section class="customer-info-section">
  <div class="customer-info-section__head">
    <h3>联系人</h3>
  </div>
  <el-table v-loading="contactPagination.loading" :data="contactPagination.rows">...</el-table>
  <div class="mt-16">
    <el-pagination ... @current-change="handleContactPageChange" @size-change="handleContactPageSizeChange" />
  </div>
</section>
```

```vue
<section class="customer-info-section">
  <div class="customer-info-section__head">
    <h3>负责销售</h3>
  </div>
  <el-table v-loading="salesPagination.loading" :data="salesPagination.rows">...</el-table>
  <div class="mt-16">
    <el-pagination ... @current-change="handleSalesPageChange" @size-change="handleSalesPageSizeChange" />
  </div>
</section>
```

- [ ] **Step 4: 运行前端构建验证 tab 结构迁移后的模板正确性**

Run: `npm run build`
Expected: `vite build` 退出码 0。

- [ ] **Step 5: 提交 Task 2**

```bash
git add frontend/src/views/CustomerCenterView.vue
git commit -m "feat: 合并客户中心客户信息页签"
```

### Task 3: 收口客户信息区块样式

**Files:**
- Modify: `frontend/src/views/CustomerCenterView.vue`
- Test: `frontend` build via `npm run build`

- [ ] **Step 1: 为客户信息区块新增统一样式类**

在页面样式中增加区块容器、标题和间距规则，保证纵向阅读节奏：

```css
.customer-info-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.customer-info-section + .customer-info-section {
  margin-top: 24px;
}

.customer-info-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.customer-info-section__head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
```

- [ ] **Step 2: 检查联系人和销售分页在同屏时的留白**

如果迁移后分页紧贴表格或区块间距不均，保持分页包裹层为：

```vue
<div class="mt-16">
  <el-pagination ... />
</div>
```

只做必要样式收口，不引入额外布局重构。

- [ ] **Step 3: 运行最终构建验证**

Run: `npm run build`
Expected: `vite build` 退出码 0。

- [ ] **Step 4: 提交 Task 3**

```bash
git add frontend/src/views/CustomerCenterView.vue
git commit -m "style: 优化客户中心客户信息区块布局"
```
