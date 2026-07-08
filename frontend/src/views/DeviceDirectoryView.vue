<template>
  <div class="page-scroll-layout">
    <div class="section-head">
      <div>
        <span class="eyebrow-dark">Device Center</span>
        <h2>设备中心</h2>
      </div>
      <div class="action-row">
        <el-button type="primary" plain @click="loadDevices">刷新设备</el-button>
      </div>
    </div>

    <section class="device-toolbar">
      <div class="toolbar-main">
        <el-input
          v-model="searchKeyword"
          class="search-input"
          placeholder="搜索设备名称 / 序列号 / 客户公司 / 联系人 / 销售"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-select v-model="serviceTypeFilter" class="service-type-select" placeholder="设备状态" @change="handleServiceTypeFilterChange">
          <el-option label="全部状态" value="all" />
          <el-option v-for="option in serviceTypeOptions" :key="option.value" :label="option.label" :value="option.value" />
        </el-select>
        <div class="action-row">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </div>
      </div>
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
    </section>

    <div class="page-table-scroll">
      <el-table v-loading="devicePagination.loading" :data="devicePagination.rows" stripe>
        <el-table-column prop="name" label="设备" min-width="180" />
        <el-table-column prop="serial_number" label="序列号" min-width="160" />
        <el-table-column label="产品型号" min-width="180" show-overflow-tooltip>
          <template #default="scope">{{ scope.row.device_model_detail?.model_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="当前保内状态" min-width="120">
          <template #default="scope">{{ scope.row.current_service_status || '-' }}</template>
        </el-table-column>
        <el-table-column label="合同开始" min-width="140">
          <template #default="scope">{{ scope.row.current_service_start_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="合同结束" min-width="140">
          <template #default="scope">{{ scope.row.current_service_end_date || '-' }}</template>
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

    <el-dialog v-model="deviceDetailVisible" title="设备详情" width="min(860px, calc(100vw - 32px))" top="4vh">
      <div class="device-detail-scroll">
        <DeviceDetailDescriptions :device="selectedDevice" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import DeviceDetailDescriptions from '../components/DeviceDetailDescriptions.vue'
import { fetchDeviceOverview, listAllResource } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'
import { SERVICE_TYPE_LABELS } from '../utils/displayMaps'
import { filterDevices } from '../utils/deviceFilters'
import { applyPaginationResponse, buildPaginationState } from '../utils/pagination'

const devices = ref([])
const deviceDetailVisible = ref(false)
const selectedDevice = ref(null)
const searchKeyword = ref('')
const statusFilter = ref('all')
const serviceTypeFilter = ref('all')
const devicePagination = buildPaginationState()

const serviceTypeOptions = Object.entries(SERVICE_TYPE_LABELS).map(([value, label]) => ({ value, label }))

const warrantyStats = computed(() => {
  const inWarranty = devices.value.filter((item) => item.current_service_status === '保内').length
  return {
    inWarranty,
    outOfWarranty: devices.value.length - inWarranty,
  }
})

const filteredDevices = computed(() => filterDevices(devices.value, {
  warrantyStatus: statusFilter.value,
  serviceType: serviceTypeFilter.value,
}))

function buildSearchParams() {
  const keyword = searchKeyword.value.trim()
  return keyword ? { search: keyword } : undefined
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
  searchKeyword.value = ''
  statusFilter.value = 'all'
  serviceTypeFilter.value = 'all'
  devicePagination.page = 1
  loadDevices()
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
    const { data } = await fetchDeviceOverview(row.id)
    selectedDevice.value = {
      ...row,
      ...data.device,
      customer: data.customer,
      customer_contact: data.customer_contact,
      sales_person: data.sales_person,
      ops_person: data.ops_person,
    }
    deviceDetailVisible.value = true
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载设备详情失败'))
  }
}

onMounted(loadDevices)
</script>

<style scoped>
.device-toolbar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 24px;
  margin-bottom: 16px;
  background: #ffffff;
  border: 1px solid #e8edf5;
  border-radius: 8px;
}

.toolbar-main {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.search-input {
  flex: 1;
  min-width: 320px;
  max-width: 680px;
}

.service-type-select {
  width: 160px;
}

.toolbar-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 18px;
  background: #f7fbff;
  border: 1px solid #dbe7f5;
  border-radius: 8px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  border-color: #7ba7d9;
  background: #f1f7ff;
}

.stat-card.is-active {
  border-color: #2f7cf6;
  background: #eaf2ff;
  box-shadow: 0 0 0 1px rgba(47, 124, 246, 0.12);
}

.stat-label {
  font-size: 13px;
  color: #5f6b7a;
}

.stat-value {
  font-size: 24px;
  color: #183153;
  line-height: 1;
}

.table-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
