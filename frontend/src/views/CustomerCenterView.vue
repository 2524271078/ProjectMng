<template>
  <div class="split-page">
    <aside class="tree-panel">
      <div class="panel-title">组织树</div>
      <el-button type="primary" plain @click="loadOrganizations">刷新组织</el-button>
      <el-input
        v-model="searchKeyword"
        class="mt-16"
        placeholder="搜索客户名称 / 区域 / 类型"
        clearable
        @keyup.enter="handleSearch"
      />
      <div class="action-row mt-16">
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>
      <el-tree
        :data="treeData"
        node-key="id"
        :props="treeProps"
        default-expand-all
        highlight-current
        @node-click="selectCustomer"
      />
    </aside>

    <section class="detail-panel">
      <div class="section-head">
        <div>
          <span class="eyebrow-dark">Customer Center</span>
          <h2>{{ selected?.name || '选择左侧客户' }}</h2>
        </div>
        <div class="action-row">
          <el-button @click="openEditDialog" :disabled="!selected">编辑组织</el-button>
          <el-button type="danger" plain @click="removeOrganization" :disabled="!selected">删除组织</el-button>
          <el-button type="primary" @click="openCreateDialog">新增组织</el-button>
        </div>
      </div>

      <el-tabs v-if="overview" v-model="activeCustomerTab" class="page-tabs-scroll" @tab-change="handleCustomerTabChange">
        <el-tab-pane label="客户信息" name="info">
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

          <section class="customer-info-section">
            <div class="customer-info-section__head">
              <h3>联系人</h3>
            </div>
            <el-table v-loading="contactPagination.loading" :data="contactPagination.rows">
              <el-table-column prop="name" label="姓名" />
              <el-table-column prop="position" label="职位" />
              <el-table-column prop="phone" label="电话" />
              <el-table-column prop="email" label="邮箱" />
            </el-table>
            <div class="mt-16">
              <el-pagination background layout="total, sizes, prev, pager, next" :current-page="contactPagination.page" :page-size="contactPagination.pageSize" :page-sizes="[10, 20, 50]" :total="contactPagination.total" @current-change="handleContactPageChange" @size-change="handleContactPageSizeChange" />
            </div>
          </section>

          <section class="customer-info-section">
            <div class="customer-info-section__head">
              <h3>负责销售</h3>
            </div>
            <el-table v-loading="salesPagination.loading" :data="salesPagination.rows">
              <el-table-column prop="name" label="销售" />
              <el-table-column prop="phone" label="电话" />
            </el-table>
            <div class="mt-16">
              <el-pagination background layout="total, sizes, prev, pager, next" :current-page="salesPagination.page" :page-size="salesPagination.pageSize" :page-sizes="[10, 20, 50]" :total="salesPagination.total" @current-change="handleSalesPageChange" @size-change="handleSalesPageSizeChange" />
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="已购设备" name="devices">
          <div class="tab-toolbar">
            <div class="tab-summary">共 {{ devicePagination.total }} 台设备</div>
            <el-input
              v-model="deviceSearchKeyword"
              class="tab-search"
              placeholder="搜索产品型号 / 设备名称 / 序列号 / 保内状态"
              clearable
              @input="handleDeviceSearch"
            />
          </div>
          <el-table v-loading="devicePagination.loading" :data="devicePagination.rows" stripe>
            <el-table-column prop="name" label="产品型号" min-width="180" />
            <el-table-column prop="serial_number" label="序列号" min-width="160" />
            <el-table-column label="设备名称" min-width="180" show-overflow-tooltip>
              <template #default="scope">{{ scope.row.device_model_detail?.model_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="current_service_status" label="当前保内状态" min-width="120" />
            <el-table-column prop="current_service_start_date" label="合同开始" min-width="140" />
            <el-table-column prop="current_service_end_date" label="合同结束" min-width="140" />
            <el-table-column label="最新服务项目" min-width="200" show-overflow-tooltip>
              <template #default="scope">{{ scope.row.latest_project?.name || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click.stop="openDeviceDetail(scope.row)">详情</el-button>
                <el-button v-if="scope.row.latest_project" link type="primary" @click.stop="openLatestDeviceProject(scope.row)">查看项目</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="mt-16">
            <el-pagination background layout="total, sizes, prev, pager, next" :current-page="devicePagination.page" :page-size="devicePagination.pageSize" :page-sizes="[10, 20, 50]" :total="devicePagination.total" @current-change="handleDevicePageChange" @size-change="handleDevicePageSizeChange" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="关联项目" name="projects">
          <el-table v-loading="projectPagination.loading" :data="projectPagination.rows" @row-click="openProjectDetail">
            <el-table-column prop="project_no" label="项目编号" min-width="150" />
            <el-table-column prop="name" label="项目名称" min-width="220" />
            <el-table-column prop="project_stage" label="阶段" min-width="120" />
            <el-table-column label="签约主体" min-width="100">
              <template #default="scope">{{ scope.row.signing_subject === 'agent' ? '代理' : '直签' }}</template>
            </el-table-column>
            <el-table-column label="销售" min-width="120">
              <template #default="scope">{{ scope.row.sales_person?.name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" min-width="120" />
          </el-table>
          <div class="mt-16">
            <el-pagination background layout="total, sizes, prev, pager, next" :current-page="projectPagination.page" :page-size="projectPagination.pageSize" :page-sizes="[10, 20, 50]" :total="projectPagination.total" @current-change="handleProjectPageChange" @size-change="handleProjectPageSizeChange" />
          </div>
        </el-tab-pane>
      </el-tabs>
      <el-empty v-else description="请选择客户查看详情" />
    </section>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑组织' : '新增组织'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="上级组织">
          <OrganizationTreeSelect v-model="form.parent" placeholder="不选则作为根组织" />
        </el-form-item>
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.org_type">
            <el-option label="客户" value="customer" />
            <el-option label="厂商" value="vendor" />
            <el-option label="集成商" value="integrator" />
            <el-option label="内部公司" value="internal_company" />
            <el-option label="第三方中标单位" value="third_party_bidder" />
          </el-select>
        </el-form-item>
        <el-form-item label="简称"><el-input v-model="form.short_name" /></el-form-item>
        <el-form-item label="区域"><el-input v-model="form.region" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="createOrganization">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="projectDrawerVisible" size="68%" title="项目详情">
      <el-tabs v-if="projectOverview" v-model="projectDetailTab" class="drawer-tabs-scroll">
        <el-tab-pane label="基础信息" name="base">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目编号">{{ projectOverview.project.project_no }}</el-descriptions-item>
            <el-descriptions-item label="项目名称">{{ projectOverview.project.name }}</el-descriptions-item>
            <el-descriptions-item label="客户公司">{{ projectOverview.customer?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="客户联系人">{{ projectOverview.customer_contact?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="联系人职位">{{ projectOverview.customer_contact?.position || '-' }}</el-descriptions-item>
            <el-descriptions-item label="实际中标公司">{{ projectOverview.project.winning_company || '-' }}</el-descriptions-item>
            <el-descriptions-item label="对接公司">{{ projectOverview.project.contact_company || '-' }}</el-descriptions-item>
            <el-descriptions-item label="签约主体">{{ projectOverview.project.signing_subject === 'agent' ? '代理' : '直签' }}</el-descriptions-item>
            <el-descriptions-item label="销售">{{ projectOverview.sales_person?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="阶段">{{ projectOverview.project.project_stage || '-' }}</el-descriptions-item>
            <el-descriptions-item label="金额">{{ projectOverview.project.amount }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <el-tab-pane label="项目设备" name="devices">
          <div class="drawer-table-scroll">
          <el-table :data="projectDeviceRows" stripe>
            <el-table-column prop="name" label="产品型号" min-width="160" />
            <el-table-column prop="serial_number" label="序列号" min-width="160" />
            <el-table-column label="设备名称" min-width="180" show-overflow-tooltip>
              <template #default="scope">{{ scope.row.device_model_detail?.model_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="device_project_type" label="项目类型" min-width="120" />
            <el-table-column label="设备状态" min-width="100">
              <template #default="scope">{{ serviceTypeLabel(scope.row.service_type) }}</template>
            </el-table-column>
            <el-table-column prop="service_start_date" label="合同开始" min-width="120" />
            <el-table-column prop="service_end_date" label="合同结束" min-width="120" />
            <el-table-column prop="service_status" label="保内状态" min-width="100" />
            <el-table-column prop="management_address" label="管理地址" min-width="180" />
            <el-table-column label="现场运维" min-width="120">
              <template #default="scope">{{ scope.row.ops_person?.name || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button link type="primary" @click.stop="openDeviceDetail(scope.row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
          </div>
          <div class="mt-16">
            <el-pagination background layout="total, sizes, prev, pager, next" :current-page="projectDeviceDrawerPagination.page" :page-size="projectDeviceDrawerPagination.pageSize" :page-sizes="[5, 10, 20]" :total="projectDeviceDrawerPagination.total" @current-change="handleProjectDeviceDrawerPageChange" @size-change="handleProjectDeviceDrawerPageSizeChange" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="项目附件" name="attachments">
          <div class="drawer-table-scroll">
            <el-table :data="projectAttachmentRows" stripe>
            <el-table-column prop="name" label="附件名" />
            <el-table-column prop="uploaded_at" label="上传时间" />
            <el-table-column label="操作" width="160">
              <template #default="scope">
                <el-button v-if="scope.row.file_url" link type="primary" @click="previewAttachment(scope.row)">预览</el-button>
                <el-button v-if="scope.row.file_url" link type="primary" @click="downloadAttachment(scope.row)">下载</el-button>
              </template>
            </el-table-column>
          </el-table>
          </div>
          <div class="mt-16">
            <el-pagination background layout="total, sizes, prev, pager, next" :current-page="projectAttachmentDrawerPagination.page" :page-size="projectAttachmentDrawerPagination.pageSize" :page-sizes="[5, 10, 20]" :total="projectAttachmentDrawerPagination.total" @current-change="handleProjectAttachmentDrawerPageChange" @size-change="handleProjectAttachmentDrawerPageSizeChange" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>

    <el-dialog v-model="deviceDetailVisible" title="设备详情" width="min(860px, calc(100vw - 32px))" top="4vh">
      <div class="device-detail-scroll">
        <DeviceDetailDescriptions :device="selectedDevice" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import OrganizationTreeSelect from '../components/OrganizationTreeSelect.vue'
import DeviceDetailDescriptions from '../components/DeviceDetailDescriptions.vue'
import {
  createResource,
  deleteResource,
  fetchCustomerContacts,
  fetchCustomerContracts,
  fetchCustomerDevices,
  fetchCustomerOverview,
  fetchCustomerProjects,
  fetchCustomerSales,
  fetchDeviceOverview,
  fetchProjectOverview,
  listResource,
  updateResource,
} from '../api/resources'
import { buildOrganizationTree } from '../utils/orgTree'
import { serviceTypeLabel } from '../utils/displayMaps'
import { applyPaginationResponse, buildPaginationState } from '../utils/pagination'

const organizations = ref([])
const selected = ref(null)
const overview = ref(null)
const activeCustomerTab = ref('info')
const contactPagination = buildPaginationState()
const salesPagination = buildPaginationState()
const devicePagination = buildPaginationState()
const contractPagination = buildPaginationState()
const projectPagination = buildPaginationState()
const projectDeviceDrawerPagination = reactive({ page: 1, pageSize: 5, total: 0 })
const projectContractDrawerPagination = reactive({ page: 1, pageSize: 5, total: 0 })
const projectAttachmentDrawerPagination = reactive({ page: 1, pageSize: 5, total: 0 })

const projectDrawerVisible = ref(false)
const projectOverview = ref(null)
const projectDetailTab = ref('base')
const deviceDetailVisible = ref(false)
const selectedDevice = ref(null)
const dialogVisible = ref(false)
const searchKeyword = ref('')
const deviceSearchKeyword = ref('')
const saving = ref(false)
const editingId = ref(null)
const form = reactive({ parent: null, name: '', org_type: 'customer', short_name: '', region: '', address: '' })
const treeProps = { label: 'name', children: 'children' }
const treeData = computed(() => buildOrganizationTree(organizations.value))
const projectDeviceRows = computed(() => paginateProjectDrawerRows(projectOverview.value?.devices || [], projectDeviceDrawerPagination))
const projectContractRows = computed(() => paginateProjectDrawerRows(projectOverview.value?.contracts || [], projectContractDrawerPagination))
const projectAttachmentRows = computed(() => paginateProjectDrawerRows(projectOverview.value?.attachments || [], projectAttachmentDrawerPagination))

function resetPaginationState(state) {
  state.page = 1
  state.pageSize = 10
  state.total = 0
  state.totalPages = 1
  state.rows = []
  state.loading = false
}

function resetCustomerTabPagination() {
  resetPaginationState(contactPagination)
  resetPaginationState(salesPagination)
  resetPaginationState(devicePagination)
  resetPaginationState(contractPagination)
  resetPaginationState(projectPagination)
}

function paginateProjectDrawerRows(rows, pagination) {
  pagination.total = rows.length
  const start = (pagination.page - 1) * pagination.pageSize
  return rows.slice(start, start + pagination.pageSize)
}

function resetProjectDrawerPagination() {
  Object.assign(projectDeviceDrawerPagination, { page: 1, pageSize: 5, total: projectOverview.value?.devices?.length || 0 })
  Object.assign(projectContractDrawerPagination, { page: 1, pageSize: 5, total: projectOverview.value?.contracts?.length || 0 })
  Object.assign(projectAttachmentDrawerPagination, { page: 1, pageSize: 5, total: projectOverview.value?.attachments?.length || 0 })
}

async function loadCustomerContactsTab() {
  if (!selected.value) return
  contactPagination.loading = true
  try {
    const { data } = await fetchCustomerContacts(selected.value.id, {
      page: contactPagination.page,
      page_size: contactPagination.pageSize,
    })
    applyPaginationResponse(contactPagination, data)
  } finally {
    contactPagination.loading = false
  }
}

async function loadCustomerSalesTab() {
  if (!selected.value) return
  salesPagination.loading = true
  try {
    const { data } = await fetchCustomerSales(selected.value.id, {
      page: salesPagination.page,
      page_size: salesPagination.pageSize,
    })
    applyPaginationResponse(salesPagination, data)
  } finally {
    salesPagination.loading = false
  }
}

async function loadCustomerDevicesTab() {
  if (!selected.value) return
  devicePagination.loading = true
  try {
    const { data } = await fetchCustomerDevices(selected.value.id, {
      page: devicePagination.page,
      page_size: devicePagination.pageSize,
      ...(deviceSearchKeyword.value.trim() ? { search: deviceSearchKeyword.value.trim() } : {}),
    })
    applyPaginationResponse(devicePagination, data)
  } finally {
    devicePagination.loading = false
  }
}

async function loadCustomerContractsTab() {
  if (!selected.value) return
  contractPagination.loading = true
  try {
    const { data } = await fetchCustomerContracts(selected.value.id, {
      page: contractPagination.page,
      page_size: contractPagination.pageSize,
    })
    applyPaginationResponse(contractPagination, data)
  } finally {
    contractPagination.loading = false
  }
}

async function loadCustomerProjectsTab() {
  if (!selected.value) return
  projectPagination.loading = true
  try {
    const { data } = await fetchCustomerProjects(selected.value.id, {
      page: projectPagination.page,
      page_size: projectPagination.pageSize,
    })
    applyPaginationResponse(projectPagination, data)
  } finally {
    projectPagination.loading = false
  }
}

async function loadActiveCustomerTab() {
  if (activeCustomerTab.value === 'info') return loadCustomerInfoTab()
  if (activeCustomerTab.value === 'devices') return loadCustomerDevicesTab()
  if (activeCustomerTab.value === 'contracts') return loadCustomerContractsTab()
  if (activeCustomerTab.value === 'projects') return loadCustomerProjectsTab()
}

async function loadCustomerInfoTab() {
  await Promise.all([
    loadCustomerContactsTab(),
    loadCustomerSalesTab(),
  ])
}

function handleCustomerTabChange() {
  loadActiveCustomerTab()
}

function handleDeviceSearch() {
  devicePagination.page = 1
  if (activeCustomerTab.value === 'devices' && selected.value) {
    loadCustomerDevicesTab()
  }
}

function handleContactPageChange(page) {
  contactPagination.page = page
  loadCustomerContactsTab()
}

function handleContactPageSizeChange(pageSize) {
  contactPagination.page = 1
  contactPagination.pageSize = pageSize
  loadCustomerContactsTab()
}

function handleSalesPageChange(page) {
  salesPagination.page = page
  loadCustomerSalesTab()
}

function handleSalesPageSizeChange(pageSize) {
  salesPagination.page = 1
  salesPagination.pageSize = pageSize
  loadCustomerSalesTab()
}

function handleDevicePageChange(page) {
  devicePagination.page = page
  loadCustomerDevicesTab()
}

function handleDevicePageSizeChange(pageSize) {
  devicePagination.page = 1
  devicePagination.pageSize = pageSize
  loadCustomerDevicesTab()
}

function handleContractPageChange(page) {
  contractPagination.page = page
  loadCustomerContractsTab()
}

function handleContractPageSizeChange(pageSize) {
  contractPagination.page = 1
  contractPagination.pageSize = pageSize
  loadCustomerContractsTab()
}

function handleProjectPageChange(page) {
  projectPagination.page = page
  loadCustomerProjectsTab()
}

function handleProjectPageSizeChange(pageSize) {
  projectPagination.page = 1
  projectPagination.pageSize = pageSize
  loadCustomerProjectsTab()
}


async function loadOrganizations() {
  try {
    const params = { org_type: 'customer', ...(searchKeyword.value.trim() ? { search: searchKeyword.value.trim() } : {}) }
    const { data } = await listResource('organizations', params)
    organizations.value = data.results || data
    if (selected.value && !organizations.value.some((item) => item.id === selected.value.id)) {
      selected.value = null
      overview.value = null
      deviceSearchKeyword.value = ''
      resetCustomerTabPagination()
    }
  } catch {
    ElMessage.error('加载客户列表失败')
  }
}

function handleSearch() {
  loadOrganizations()
}

function resetSearch() {
  searchKeyword.value = ''
  loadOrganizations()
}

async function selectCustomer(node) {
  selected.value = node
  activeCustomerTab.value = 'info'
  deviceSearchKeyword.value = ''
  resetCustomerTabPagination()
  const { data } = await fetchCustomerOverview(node.id)
  overview.value = data
  await loadCustomerInfoTab()
}

async function openProjectDetail(row) {
  const { data } = await fetchProjectOverview(row.id)
  projectOverview.value = data
  projectDetailTab.value = 'base'
  resetProjectDrawerPagination()
  projectDrawerVisible.value = true
}

function openLatestDeviceProject(device) {
  if (!device.latest_project?.id) {
    ElMessage.info('该设备尚未关联项目')
    return
  }
  openProjectDetail(device.latest_project)
}

async function openDeviceDetail(device) {
  const { data } = await fetchDeviceOverview(device.device_id || device.id)
  selectedDevice.value = {
    ...device,
    ...data.device,
    customer: data.customer,
    customer_contact: data.customer_contact,
    sales_person: data.sales_person,
    ops_person: data.ops_person,
  }
  deviceDetailVisible.value = true
}

function handleProjectDeviceDrawerPageChange(page) {
  projectDeviceDrawerPagination.page = page
}

function handleProjectDeviceDrawerPageSizeChange(pageSize) {
  projectDeviceDrawerPagination.page = 1
  projectDeviceDrawerPagination.pageSize = pageSize
}

function handleProjectContractDrawerPageChange(page) {
  projectContractDrawerPagination.page = page
}

function handleProjectContractDrawerPageSizeChange(pageSize) {
  projectContractDrawerPagination.page = 1
  projectContractDrawerPagination.pageSize = pageSize
}

function handleProjectAttachmentDrawerPageChange(page) {
  projectAttachmentDrawerPagination.page = page
}

function handleProjectAttachmentDrawerPageSizeChange(pageSize) {
  projectAttachmentDrawerPagination.page = 1
  projectAttachmentDrawerPagination.pageSize = pageSize
}

function previewAttachment(row) {
  window.open(row.file_url, '_blank', 'noopener,noreferrer')
}

function downloadAttachment(row) {
  const link = document.createElement('a')
  link.href = row.file_url
  link.download = row.name || '附件'
  link.target = '_blank'
  link.click()
}

function openCreateDialog() {
  editingId.value = null
  resetForm()
  form.parent = selected.value?.id || null
  dialogVisible.value = true
}

function openEditDialog() {
  if (!selected.value) return
  editingId.value = selected.value.id
  Object.assign(form, {
    parent: selected.value.parent || null,
    name: selected.value.name || '',
    org_type: selected.value.org_type || 'customer',
    short_name: selected.value.short_name || '',
    region: selected.value.region || '',
    address: selected.value.address || '',
  })
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(form, { parent: null, name: '', org_type: 'customer', short_name: '', region: '', address: '' })
}

function buildPayload() {
  const payload = { ...form }
  if (!payload.parent) delete payload.parent
  return payload
}

async function createOrganization() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写组织名称')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateResource('organizations', editingId.value, buildPayload())
    } else {
      await createResource('organizations', buildPayload())
    }
    ElMessage.success(editingId.value ? '组织已更新' : '组织已新增')
    dialogVisible.value = false
    resetForm()
    editingId.value = null
    await loadOrganizations()
  } catch {
    ElMessage.error('保存组织失败，请检查必填项')
  } finally {
    saving.value = false
  }
}

async function removeOrganization() {
  if (!selected.value) return
  await ElMessageBox.confirm(`确认删除组织“${selected.value.name}”？`, '删除确认', { type: 'warning' })
  await deleteResource('organizations', selected.value.id)
  ElMessage.success('组织已删除')
  selected.value = null
  overview.value = null
  projectOverview.value = null
  projectDrawerVisible.value = false
  activeCustomerTab.value = 'info'
  deviceSearchKeyword.value = ''
  resetCustomerTabPagination()
  await loadOrganizations()
}

onMounted(loadOrganizations)
</script>

<style scoped>
.customer-info-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  border: 1px solid #e6ebf2;
  border-radius: 16px;
  background: #fff;
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
  color: #1f2a37;
}

.tab-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.tab-summary {
  font-size: 13px;
  color: #5f6b7a;
}

.tab-search {
  width: min(360px, 100%);
}
</style>
