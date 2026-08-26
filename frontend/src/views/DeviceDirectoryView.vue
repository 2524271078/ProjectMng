<template>
  <div class="page-scroll-layout">
    <div class="section-head">
      <div>
        <span class="eyebrow-dark">Device Center</span>
        <h2>设备资产</h2>
      </div>
      <div class="action-row">
        <el-button @click="loadDevices">刷新设备</el-button>
      </div>
    </div>

    <section class="device-toolbar">
      <div v-if="dashboardFilterLabel" class="dashboard-filter-banner">
        <span>当前工作台筛选：<strong>{{ dashboardFilterLabel }}</strong></span>
        <el-button link type="primary" @click="clearDashboardFilter">清除筛选</el-button>
      </div>
      <div class="toolbar-main">
        <div class="toolbar-search-fields">
          <el-input
            v-model="deviceNameKeyword"
            class="search-input"
            placeholder="设备名称"
            clearable
            @keyup.enter="handleSearch"
          />
          <el-input
            v-model="customerNameKeyword"
            class="search-input"
            placeholder="客户公司"
            clearable
            @keyup.enter="handleSearch"
          />
          <el-input
            v-model="salesNameKeyword"
            class="search-input"
            placeholder="销售"
            clearable
            @keyup.enter="handleSearch"
          />
          <el-input
            v-model="softwareVersionKeyword"
            class="search-input"
            placeholder="系统版本"
            clearable
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="toolbar-filter-actions">
          <div class="toolbar-stats">
            <button
              type="button"
              class="stat-card"
              :class="{ 'is-active': statusFilter === 'all' }"
              @click="setStatusFilter('all')"
            >
              <span class="stat-label">设备总数</span>
              <strong class="stat-value">{{ devices.length }}</strong>
            </button>
            <button
              type="button"
              class="stat-card"
              :class="{ 'is-active': statusFilter === 'in' }"
              @click="setStatusFilter('in')"
            >
              <span class="stat-label">保内设备</span>
              <strong class="stat-value">{{ warrantyStats.inWarranty }}</strong>
            </button>
            <button
              type="button"
              class="stat-card"
              :class="{ 'is-active': statusFilter === 'out' }"
              @click="setStatusFilter('out')"
            >
              <span class="stat-label">保外设备</span>
              <strong class="stat-value">{{ warrantyStats.outOfWarranty }}</strong>
            </button>
          </div>
          <el-select v-model="serviceTypeFilter" class="service-type-select" placeholder="设备状态" @change="handleServiceTypeFilterChange">
            <el-option label="全部状态" value="all" />
            <el-option v-for="option in serviceTypeOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
          <el-select v-model="signingSubjectFilter" class="service-type-select" placeholder="签约主体" @change="handleSigningSubjectFilterChange">
            <el-option label="全部签约主体" value="all" />
            <el-option label="直签" value="direct" />
            <el-option label="代理" value="agent" />
          </el-select>
          <div class="action-row">
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </div>
        </div>
      </div>
    </section>

    <div class="page-table-scroll">
      <el-table v-loading="devicePagination.loading" :data="devicePagination.rows" height="100%">
        <el-table-column label="设备名称" min-width="180" show-overflow-tooltip>
          <template #default="scope">{{ scope.row.device_model_detail?.model_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="当前保内状态" min-width="120">
          <template #default="scope"><el-tag :type="serviceStatusTagType(scope.row.current_service_status)" effect="light">{{ scope.row.current_service_status || '-' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="合同开始" min-width="140">
          <template #default="scope">{{ scope.row.current_service_start_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="合同结束" min-width="140">
          <template #default="scope">{{ scope.row.current_service_end_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="签约主体" min-width="110">
          <template #default="scope">{{ signingSubjectLabel(scope.row.current_signing_subject) }}</template>
        </el-table-column>
        <el-table-column label="客户公司" min-width="200">
          <template #default="scope">{{ scope.row.customer_org_detail?.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="客户联系人" min-width="160">
          <template #default="scope">{{ scope.row.customer_contact_detail?.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="销售" min-width="140">
          <template #default="scope">{{ scope.row.sales_person_detail?.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click.stop="openDeviceDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="table-pagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next"
        :current-page="devicePagination.page"
        :page-size="devicePagination.pageSize"
        :page-sizes="[10, 20, 50]"
        :total="devicePagination.total"
        @current-change="handlePageChange"
        @size-change="handlePageSizeChange"
      />
    </div>

    <el-dialog v-model="deviceDetailVisible" title="设备详情" width="min(1100px, calc(100vw - 32px))" top="4vh">
      <div class="device-detail-scroll">
        <el-tabs v-model="deviceDetailTab">
          <el-tab-pane label="基础信息" name="basic">
            <DeviceDetailDescriptions :device="selectedDevice" />
          </el-tab-pane>
          <el-tab-pane label="服务管理" name="service-management">
            <DeviceServiceWorkspace
              v-if="selectedDevice?.id"
              :device-id="selectedDevice.id"
              :project-devices="selectedDevice.project_devices || []"
            />
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <el-dialog v-model="operationRecordDialogVisible" title="新增设备运维记录" width="680px" append-to-body>
      <el-form label-width="110px">
        <el-form-item label="服务计划" required>
          <el-select v-model="operationRecordForm.servicePlanId" placeholder="请选择服务计划" class="form-select" @change="handleOperationPlanChange">
            <el-option v-for="item in deviceServicePlans" :key="item.id" :label="item.project_device_detail?.project_name || `服务计划 #${item.id}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="服务类型" required>
          <el-select v-model="operationRecordForm.recordType" class="form-select">
            <el-option label="巡检" value="inspection" />
            <el-option label="系统升级" value="system_upgrade" />
            <el-option label="规则库升级" value="rule_library_upgrade" />
            <el-option label="故障处理" value="fault_handling" />
            <el-option label="配置变更" value="configuration_change" />
            <el-option label="技术支持" value="technical_support" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="operationRecordForm.recordType === 'inspection'" label="关联巡检任务">
          <el-select v-model="operationRecordForm.inspectionTaskId" clearable placeholder="可选：完成任务后自动闭环" class="form-select">
            <el-option v-for="item in availableInspectionTasks" :key="item.id" :label="`${item.planned_date}（${inspectionTaskStatusLabel(item.status)}）`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="服务时间" required>
          <el-date-picker v-model="operationRecordForm.performedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" class="form-select" />
        </el-form-item>
        <el-form-item label="处理结论">
          <el-select v-model="operationRecordForm.result" class="form-select">
            <el-option label="正常" value="normal" />
            <el-option label="发现问题" value="issue_found" />
            <el-option label="需跟进" value="follow_up" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题描述"><el-input v-model="operationRecordForm.issueDescription" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="处理措施"><el-input v-model="operationRecordForm.resolution" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="升级后系统版本"><el-input v-model="operationRecordForm.softwareVersionAfter" /></el-form-item>
        <el-form-item label="升级后规则库版本"><el-input v-model="operationRecordForm.ruleLibraryVersionAfter" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="operationRecordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="operationRecordSaving" @click="saveOperationRecord">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="servicePlanDialogVisible" title="配置设备服务计划" width="620px" append-to-body>
      <el-form label-width="120px">
        <el-form-item label="项目服务周期" required>
          <el-select v-model="servicePlanForm.projectDeviceId" placeholder="请选择项目服务周期" class="form-select">
            <el-option
              v-for="item in selectedDevice?.project_devices || []"
              :key="item.id"
              :label="`${item.project_name}（${item.service_start_date || '-'} 至 ${item.service_end_date || '-'}）`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="服务标准模板">
          <el-select v-model="servicePlanForm.templateId" clearable placeholder="可选：选择后按模板生成规则" class="form-select">
            <el-option v-for="item in serviceStandardTemplates" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="首次巡检日期">
          <el-date-picker v-model="servicePlanForm.firstInspectionDate" type="date" value-format="YYYY-MM-DD" placeholder="未填则以服务开始日为准" class="form-select" />
        </el-form-item>
        <el-form-item label="巡检频率" required>
          <el-select v-model="servicePlanForm.inspectionFrequency" class="form-select">
            <el-option label="每月" value="monthly" />
            <el-option label="每季度" value="quarterly" />
            <el-option label="每半年" value="semiannual" />
            <el-option label="每年" value="annual" />
            <el-option label="自定义天数" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="servicePlanForm.inspectionFrequency === 'custom'" label="巡检间隔" required>
          <el-input-number v-model="servicePlanForm.inspectionIntervalDays" :min="1" class="form-select" />
          <span class="form-suffix">天</span>
        </el-form-item>
        <el-form-item label="提前提醒" required>
          <el-input-number v-model="servicePlanForm.reminderDays" :min="0" class="form-select" />
          <span class="form-suffix">天</span>
        </el-form-item>
        <el-form-item label="服务内容">
          <el-checkbox-group v-model="servicePlanForm.serviceContents">
            <el-checkbox label="inspection">巡检</el-checkbox>
            <el-checkbox label="system_upgrade">系统升级</el-checkbox>
            <el-checkbox label="rule_library_upgrade">规则库升级</el-checkbox>
            <el-checkbox label="technical_support">技术支持</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="servicePlanDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="servicePlanSaving" @click="saveServicePlan">保存并生成服务任务</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="serviceScheduleDialogVisible" title="新增服务项计划" width="560px" append-to-body>
      <el-form label-width="110px">
        <el-form-item label="服务项" required><el-select v-model="serviceScheduleForm.serviceType" class="form-select"><el-option label="巡检" value="inspection" /><el-option label="系统升级" value="system_upgrade" /><el-option label="规则库升级" value="rule_library_upgrade" /></el-select></el-form-item>
        <el-form-item label="首次执行日期"><el-date-picker v-model="serviceScheduleForm.firstServiceDate" type="date" value-format="YYYY-MM-DD" class="form-select" /></el-form-item>
        <el-form-item label="执行频率" required><el-select v-model="serviceScheduleForm.frequency" class="form-select"><el-option label="每月" value="monthly" /><el-option label="每季度" value="quarterly" /><el-option label="每半年" value="semiannual" /><el-option label="每年" value="annual" /><el-option label="自定义天数" value="custom" /></el-select></el-form-item>
        <el-form-item v-if="serviceScheduleForm.frequency === 'custom'" label="执行间隔" required><el-input-number v-model="serviceScheduleForm.intervalDays" :min="1" /></el-form-item>
        <el-form-item label="提前提醒"><el-input-number v-model="serviceScheduleForm.reminderDays" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="serviceScheduleDialogVisible = false">取消</el-button><el-button type="primary" :loading="serviceScheduleSaving" @click="saveServiceSchedule">保存并生成任务</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import DeviceDetailDescriptions from '../components/DeviceDetailDescriptions.vue'
import DeviceServiceWorkspace from '../components/DeviceServiceWorkspace.vue'
import { createResource, fetchDeviceOverview, listAllResource } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'
import { INSPECTION_TASK_STATUS_LABELS, OPERATION_RECORD_TYPE_LABELS, SERVICE_TYPE_LABELS, signingSubjectLabel } from '../utils/displayMaps'
import { filterDevices } from '../utils/deviceFilters'
import { formatLocalDateTime } from '../utils/localDateTime'
import { applyPaginationResponse, buildPaginationState } from '../utils/pagination'

const devices = ref([])
const deviceDetailVisible = ref(false)
const selectedDevice = ref(null)
const deviceDetailTab = ref('basic')
const deviceServicePlans = ref([])
const deviceServiceSchedules = ref([])
const deviceInspectionTasks = ref([])
const deviceOperationRecords = ref([])
const servicePlanDialogVisible = ref(false)
const servicePlanSaving = ref(false)
const serviceStandardTemplates = ref([])
const servicePlanForm = reactive({ projectDeviceId: null, templateId: null, firstInspectionDate: '', inspectionFrequency: 'quarterly', inspectionIntervalDays: null, reminderDays: 7, serviceContents: ['inspection'] })
const serviceScheduleDialogVisible = ref(false)
const serviceScheduleSaving = ref(false)
const serviceScheduleForm = reactive({ serviceType: 'system_upgrade', firstServiceDate: '', frequency: 'semiannual', intervalDays: null, reminderDays: 7 })
const operationRecordDialogVisible = ref(false)
const operationRecordSaving = ref(false)
const operationRecordForm = reactive({ servicePlanId: null, projectDeviceId: null, inspectionTaskId: null, recordType: 'inspection', performedAt: '', result: 'normal', issueDescription: '', resolution: '', softwareVersionAfter: '', ruleLibraryVersionAfter: '' })
const deviceNameKeyword = ref('')
const customerNameKeyword = ref('')
const salesNameKeyword = ref('')
const softwareVersionKeyword = ref('')
const statusFilter = ref('all')
const serviceTypeFilter = ref('all')
const signingSubjectFilter = ref('all')
const dashboardFilter = ref('')
const serviceEndFrom = ref('')
const serviceEndTo = ref('')
const dashboardCustomerId = ref('')
const devicePagination = buildPaginationState()
const route = useRoute()
const router = useRouter()

const serviceTypeOptions = Object.entries(SERVICE_TYPE_LABELS).map(([value, label]) => ({ value, label }))
const inspectionFrequencyLabels = { monthly: '每月', quarterly: '每季度', semiannual: '每半年', annual: '每年', custom: '自定义天数' }
const serviceContentLabels = { inspection: '巡检', system_upgrade: '系统升级', rule_library_upgrade: '规则库升级', technical_support: '技术支持', fault_handling: '故障处理' }

const warrantyStats = computed(() => {
  const inWarranty = devices.value.filter((item) => item.current_service_status === '保内').length
  return {
    inWarranty,
    outOfWarranty: devices.value.length - inWarranty,
  }
})
const availableInspectionTasks = computed(() => deviceInspectionTasks.value.filter((item) => (
  item.service_plan === operationRecordForm.servicePlanId
  && item.task_type === operationRecordForm.recordType
  && item.status !== 'completed'
  && item.status !== 'cancelled'
)))
const dashboardFilterLabel = computed(() => {
  const labels = {
    in_warranty: '在保设备',
    in_warranty_long: '在保（180天后到期）',
    expiring_30: '30天内到期',
    expiring_180: '31-180天到期',
    expired: '已过保',
    unmaintained: '未维护服务期',
  }
  if (dashboardCustomerId.value) return '指定客户设备'
  if (serviceEndFrom.value || serviceEndTo.value) return '指定月份到期设备'
  return labels[dashboardFilter.value] || ''
})

const filteredDevices = computed(() => filterDevices(devices.value, {
  warrantyStatus: statusFilter.value,
  serviceType: serviceTypeFilter.value,
  signingSubject: signingSubjectFilter.value,
}))

function buildSearchParams() {
  const deviceName = deviceNameKeyword.value.trim()
  const customerName = customerNameKeyword.value.trim()
  const salesName = salesNameKeyword.value.trim()
  const softwareVersion = softwareVersionKeyword.value.trim()
  return {
    ...(deviceName ? { device_name: deviceName } : {}),
    ...(customerName ? { customer_name: customerName } : {}),
    ...(salesName ? { sales_name: salesName } : {}),
    ...(softwareVersion ? { software_version: softwareVersion } : {}),
    ...(dashboardFilter.value && dashboardFilter.value !== 'all' ? { overview_filter: dashboardFilter.value } : {}),
    ...(serviceEndFrom.value ? { service_end_from: serviceEndFrom.value } : {}),
    ...(serviceEndTo.value ? { service_end_to: serviceEndTo.value } : {}),
    ...(dashboardCustomerId.value ? { customer_id: dashboardCustomerId.value } : {}),
  }
}

function syncDashboardFiltersFromRoute() {
  dashboardFilter.value = String(route.query.overview_filter || '').trim()
  serviceEndFrom.value = String(route.query.service_end_from || '').trim()
  serviceEndTo.value = String(route.query.service_end_to || '').trim()
  dashboardCustomerId.value = String(route.query.customer_id || '').trim()
  const warrantyFilterMap = {
    in_warranty: 'in',
    in_warranty_long: 'in',
    expiring_30: 'in',
    expiring_180: 'in',
    expired: 'out',
    unmaintained: 'out',
  }
  statusFilter.value = warrantyFilterMap[dashboardFilter.value] || 'all'
}

function clearDashboardFilter() {
  router.replace({ path: route.path })
}

function syncDevicePagination() {
  const total = filteredDevices.value.length
  const totalPages = total ? Math.ceil(total / devicePagination.pageSize) : 1
  if (devicePagination.page > totalPages) {
    devicePagination.page = totalPages
  }
  const start = (devicePagination.page - 1) * devicePagination.pageSize
  const end = start + devicePagination.pageSize
  applyPaginationResponse(devicePagination, {
    count: total,
    page: devicePagination.page,
    page_size: devicePagination.pageSize,
    total_pages: totalPages,
    results: filteredDevices.value.slice(start, end),
  })
}

function setStatusFilter(nextFilter) {
  statusFilter.value = nextFilter
  devicePagination.page = 1
  syncDevicePagination()
}

function handleServiceTypeFilterChange() {
  devicePagination.page = 1
  syncDevicePagination()
}

function handleSigningSubjectFilterChange() {
  devicePagination.page = 1
  syncDevicePagination()
}

async function loadDevices() {
  devicePagination.loading = true
  try {
    const { data } = await listAllResource('devices', buildSearchParams())
    devices.value = unwrapList(data)
    syncDevicePagination()
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载设备列表失败'))
  } finally {
    devicePagination.loading = false
  }
}

function handleSearch() {
  devicePagination.page = 1
  loadDevices()
}

function resetSearch() {
  deviceNameKeyword.value = ''
  customerNameKeyword.value = ''
  salesNameKeyword.value = ''
  softwareVersionKeyword.value = ''
  statusFilter.value = 'all'
  serviceTypeFilter.value = 'all'
  signingSubjectFilter.value = 'all'
  devicePagination.page = 1
  if (Object.keys(route.query).length) {
    clearDashboardFilter()
  } else {
    loadDevices()
  }
}

function handlePageChange(page) {
  devicePagination.page = page
  syncDevicePagination()
}

function handlePageSizeChange(pageSize) {
  devicePagination.page = 1
  devicePagination.pageSize = pageSize
  syncDevicePagination()
}

async function openDeviceDetail(row) {
  try {
    const [{ data }, plansResponse, tasksResponse, recordsResponse] = await Promise.all([
      fetchDeviceOverview(row.id),
      listAllResource('device-service-plans', { device: row.id }),
      listAllResource('inspection-tasks', { device: row.id }),
      listAllResource('device-operation-records', { device: row.id }),
    ])
    selectedDevice.value = {
      ...row,
      ...data.device,
      customer: data.customer,
      customer_contact: data.customer_contact,
      sales_person: data.sales_person,
      ops_person: data.ops_person,
    }
    deviceServicePlans.value = unwrapList(plansResponse.data)
    const scheduleResponses = await Promise.all(deviceServicePlans.value.map((plan) => listAllResource('device-service-schedules', { service_plan: plan.id })))
    deviceServiceSchedules.value = scheduleResponses.flatMap((response) => unwrapList(response.data))
    deviceInspectionTasks.value = unwrapList(tasksResponse.data)
    deviceOperationRecords.value = unwrapList(recordsResponse.data)
    selectedDevice.value.project_devices = data.project_devices || []
    deviceDetailTab.value = 'basic'
    deviceDetailVisible.value = true
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载设备详情失败'))
  }
}

async function openServicePlanDialog() {
  if (!(selectedDevice.value?.project_devices || []).length) {
    ElMessage.warning('当前设备尚未绑定项目服务周期，无法配置服务计划')
    return
  }
  servicePlanForm.projectDeviceId = selectedDevice.value.project_devices[0].id
  servicePlanForm.templateId = null
  servicePlanForm.firstInspectionDate = ''
  servicePlanForm.inspectionFrequency = 'quarterly'
  servicePlanForm.inspectionIntervalDays = null
  servicePlanForm.reminderDays = 7
  servicePlanForm.serviceContents = ['inspection']
  try {
    const { data } = await listAllResource('service-standard-templates')
    serviceStandardTemplates.value = unwrapList(data)
    servicePlanDialogVisible.value = true
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载服务标准模板失败'))
  }
}

async function saveServicePlan() {
  if (!servicePlanForm.projectDeviceId) {
    ElMessage.warning('请选择项目服务周期')
    return
  }
  if (servicePlanForm.inspectionFrequency === 'custom' && !servicePlanForm.inspectionIntervalDays) {
    ElMessage.warning('请填写自定义巡检间隔天数')
    return
  }
  servicePlanSaving.value = true
  try {
    const payload = {
      project_device: servicePlanForm.projectDeviceId,
      ...(servicePlanForm.templateId ? { template: servicePlanForm.templateId } : {}),
      ...(servicePlanForm.firstInspectionDate ? { first_inspection_date: servicePlanForm.firstInspectionDate } : {}),
      inspection_frequency: servicePlanForm.inspectionFrequency,
      ...(servicePlanForm.inspectionFrequency === 'custom' ? { inspection_interval_days: servicePlanForm.inspectionIntervalDays } : {}),
      reminder_days: servicePlanForm.reminderDays,
      service_contents: servicePlanForm.serviceContents,
      }
      await createResource('device-service-plans', payload)
      servicePlanDialogVisible.value = false
      ElMessage.success('服务计划已保存，巡检任务已生成')
    } catch (error) {
      ElMessage.error(formatApiError(error, '保存服务计划失败'))
      return
    } finally {
      servicePlanSaving.value = false
    }
    try {
      const { data } = await listAllResource('device-service-plans', { device: selectedDevice.value.id })
      deviceServicePlans.value = unwrapList(data)
      const scheduleResponses = await Promise.all(deviceServicePlans.value.map((plan) => listAllResource('device-service-schedules', { service_plan: plan.id })))
      deviceServiceSchedules.value = scheduleResponses.flatMap((response) => unwrapList(response.data))
    } catch (error) {
      ElMessage.warning('服务计划已保存，但列表刷新失败，请关闭后重新打开设备详情')
    }
  }

function openOperationRecordDialog() {
  if (!deviceServicePlans.value.length) {
    ElMessage.warning('请先配置服务计划')
    return
  }
  operationRecordForm.servicePlanId = deviceServicePlans.value[0].id
  operationRecordForm.projectDeviceId = deviceServicePlans.value[0].project_device
  operationRecordForm.inspectionTaskId = null
  operationRecordForm.recordType = 'inspection'
  operationRecordForm.performedAt = formatLocalDateTime()
  operationRecordForm.result = 'normal'
  operationRecordForm.issueDescription = ''
  operationRecordForm.resolution = ''
  operationRecordForm.softwareVersionAfter = ''
  operationRecordForm.ruleLibraryVersionAfter = ''
  operationRecordDialogVisible.value = true
}

function openServiceScheduleDialog() {
  Object.assign(serviceScheduleForm, { serviceType: 'system_upgrade', firstServiceDate: '', frequency: 'semiannual', intervalDays: null, reminderDays: 7 })
  serviceScheduleDialogVisible.value = true
}

async function saveServiceSchedule() {
  const plan = deviceServicePlans.value[0]
  if (!plan) return
  if (serviceScheduleForm.frequency === 'custom' && !serviceScheduleForm.intervalDays) {
    ElMessage.warning('请填写自定义执行间隔天数')
    return
  }
  serviceScheduleSaving.value = true
  try {
    await createResource('device-service-schedules', {
      service_plan: plan.id,
      service_type: serviceScheduleForm.serviceType,
      frequency: serviceScheduleForm.frequency,
      ...(serviceScheduleForm.firstServiceDate ? { first_service_date: serviceScheduleForm.firstServiceDate } : {}),
      ...(serviceScheduleForm.frequency === 'custom' ? { interval_days: serviceScheduleForm.intervalDays } : {}),
      reminder_days: serviceScheduleForm.reminderDays,
    })
    serviceScheduleDialogVisible.value = false
    ElMessage.success('服务项计划已保存，任务已生成')
  } catch (error) {
    ElMessage.error(formatApiError(error, '保存服务项计划失败'))
    return
  } finally {
    serviceScheduleSaving.value = false
  }
  const { data } = await listAllResource('device-service-schedules', { service_plan: plan.id })
  deviceServiceSchedules.value = unwrapList(data)
}

function handleOperationPlanChange(planId) {
  const plan = deviceServicePlans.value.find((item) => item.id === planId)
  operationRecordForm.projectDeviceId = plan?.project_device || null
  operationRecordForm.inspectionTaskId = null
}

async function saveOperationRecord() {
  if (!operationRecordForm.servicePlanId || !operationRecordForm.projectDeviceId || !operationRecordForm.performedAt) {
    ElMessage.warning('请填写服务计划和服务时间')
    return
  }
  operationRecordSaving.value = true
  try {
    const payload = {
      device: selectedDevice.value.id,
      project_device: operationRecordForm.projectDeviceId,
      service_plan: operationRecordForm.servicePlanId,
      record_type: operationRecordForm.recordType,
      performed_at: operationRecordForm.performedAt,
      result: operationRecordForm.result,
      issue_description: operationRecordForm.issueDescription,
      resolution: operationRecordForm.resolution,
      software_version_after: operationRecordForm.softwareVersionAfter,
      rule_library_version_after: operationRecordForm.ruleLibraryVersionAfter,
      ...(operationRecordForm.inspectionTaskId ? { inspection_task: operationRecordForm.inspectionTaskId } : {}),
    }
    await createResource('device-operation-records', payload)
    const [tasksResponse, recordsResponse] = await Promise.all([
      listAllResource('inspection-tasks', { device: selectedDevice.value.id }),
      listAllResource('device-operation-records', { device: selectedDevice.value.id }),
    ])
    deviceInspectionTasks.value = unwrapList(tasksResponse.data)
    deviceOperationRecords.value = unwrapList(recordsResponse.data)
    operationRecordDialogVisible.value = false
    ElMessage.success('运维记录已保存')
  } catch (error) {
    ElMessage.error(formatApiError(error, '保存运维记录失败'))
  } finally {
    operationRecordSaving.value = false
  }
}

function inspectionFrequencyLabel(value) {
  return inspectionFrequencyLabels[value] || value || '-'
}

function serviceContentsLabel(values) {
  if (!Array.isArray(values) || !values.length) return '-'
  return values.map((value) => serviceContentLabels[value] || value).join('、')
}

function serviceStatusTagType(status) {
  if (status === '保内') return 'success'
  if (status === '已过保' || status === '未维护服务期') return 'danger'
  return 'warning'
}

function inspectionTaskStatusLabel(value) {
  return INSPECTION_TASK_STATUS_LABELS[value] || value || '-'
}

function operationRecordTypeLabel(value) {
  return OPERATION_RECORD_TYPE_LABELS[value] || value || '-'
}

watch(
  () => route.query,
  () => {
    syncDashboardFiltersFromRoute()
    devicePagination.page = 1
    loadDevices()
  },
  { immediate: true },
)
</script>

<style scoped>
.device-toolbar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 18px;
  margin-bottom: 12px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-lg);
}

.toolbar-main {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dashboard-filter-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  border: 1px solid #cce0da;
  border-radius: var(--app-radius);
  background: var(--app-primary-soft);
  color: #4d6660;
  font-size: 13px;
}

.dashboard-filter-banner strong {
  color: #12645c;
}

.toolbar-search-fields {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.toolbar-filter-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 10px;
  border-top: 1px solid #edf0ed;
}

.search-input {
  width: 100%;
  min-width: 0;
}

.toolbar-filter-actions .action-row {
  flex-wrap: nowrap;
}

.service-type-select {
  width: 160px;
}

.toolbar-stats {
  display: flex;
  gap: 6px;
  flex: 0 0 auto;
}

.stat-card {
  position: relative;
  display: flex;
  min-height: 36px;
  align-items: center;
  gap: 7px;
  padding: 0 10px;
  overflow: hidden;
  background: #fafbf9;
  border: 1px solid var(--app-border);
  border-radius: 999px;
  text-align: left;
  cursor: pointer;
  transition: border-color var(--app-transition), background-color var(--app-transition), transform var(--app-transition);
}

.stat-card:hover {
  border-color: #c7d9d3;
  background: #f5f8f6;
  transform: translateY(-1px);
}

.stat-card.is-active {
  border-color: #9cc5ba;
  background: var(--app-primary-soft);
}

.stat-label {
  color: var(--app-subtle);
  font-size: 12px;
}

.stat-value {
  color: var(--app-ink);
  font-size: 17px;
  font-weight: 670;
  letter-spacing: -.035em;
  line-height: .95;
}

.table-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.service-tab-action {
  display: flex;
  justify-content: flex-end;
  margin: 0 0 12px;
}

.service-schedule-table {
  margin-top: 12px;
}

.form-select {
  width: 100%;
}

.form-suffix {
  margin-left: 8px;
  white-space: nowrap;
  color: var(--app-subtle);
}

@media (max-width: 1100px) {
  .toolbar-search-fields { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (min-width: 1600px) {
  .toolbar-main {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: end;
  }
  .toolbar-filter-actions {
    justify-content: flex-end;
    padding-top: 0;
    border-top: 0;
  }
}

@media (max-width: 720px) {
  .section-head, .toolbar-filter-actions { align-items: flex-start; flex-direction: column; }
  .toolbar-filter-actions { width: 100%; }
  .toolbar-filter-actions .action-row { width: 100%; }
  .toolbar-search-fields { grid-template-columns: 1fr; }
  .toolbar-stats { width: 100%; flex-wrap: wrap; }
  .service-type-select { width: 100%; }
}

</style>
