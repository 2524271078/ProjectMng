<template>
  <div class="dashboard">
    <section class="overview-section" v-loading="overviewLoading">
      <div class="section-title">
        <div>
          <span class="eyebrow-dark">OVERVIEW</span>
          <h2>设备服务总览</h2>
        </div>
        <span class="section-title__hint">统计范围与当前账号的数据权限一致</span>
      </div>
      <div class="metric-grid">
        <button v-for="item in metricCards" :key="item.key" type="button" class="metric-card" :class="`metric-card--${item.key}`" @click="handleMetricClick(item)">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.desc }}</p>
        </button>
      </div>
    </section>

    <el-row :gutter="18" class="dashboard-row">
      <el-col :xs="24" :lg="15">
        <el-card class="todo-card" shadow="never" v-loading="loading">
          <template #header>
            <div class="todo-card__header">
              <span>待办提醒</span>
              <div class="todo-card__tools">
                <el-select v-model="reminderTypeFilter" class="todo-type-filter" @change="reminderPage = 1">
                  <el-option label="全部分类" value="all" />
                  <el-option label="服务任务" value="service_task" />
                  <el-option label="服务即将到期" value="service_expiring" />
                </el-select>
                <el-tag type="danger" effect="light">{{ filteredReminders.length }}</el-tag>
              </div>
            </div>
          </template>
          <el-empty v-if="!filteredReminders.length" description="暂无待办提醒" :image-size="72" />
          <template v-else>
            <div class="todo-table-scroll">
              <el-table :data="paginatedReminders" size="small">
                <el-table-column label="类型" width="150">
                  <template #default="scope"><el-tag :type="scope.row.type === 'service_expiring' ? 'warning' : 'danger'">{{ reminderTypeLabel(scope.row.type) }}</el-tag></template>
                </el-table-column>
                <el-table-column prop="content" label="待办内容" min-width="360" />
                <el-table-column prop="target_date" label="日期" width="130" />
                <el-table-column label="剩余" width="100">
                  <template #default="scope">{{ daysLeftLabel(scope.row.days_left) }}</template>
                </el-table-column>
                <el-table-column label="操作" width="80" fixed="right">
                  <template #default="scope"><el-button link type="primary" @click="confirmReminder(scope.row)">确认</el-button></template>
                </el-table-column>
              </el-table>
            </div>
            <div class="todo-pagination">
              <el-pagination background small layout="total, prev, pager, next" :current-page="reminderPage" :page-size="reminderPageSize" :total="filteredReminders.length" @current-change="reminderPage = $event" />
            </div>
          </template>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="chart-card service-chart-card" shadow="never" v-loading="overviewLoading">
          <template #header>
            <div class="card-title">
              <span>设备服务状态</span>
              <small>按当前服务周期</small>
            </div>
          </template>
          <div class="service-chart-content">
            <div class="donut-chart" :style="{ background: statusChartBackground }">
              <div class="donut-chart__center"><strong>{{ overview.metrics.devices_total }}</strong><span>台设备</span></div>
            </div>
            <div class="status-legend">
              <button v-for="item in overview.service_status" :key="item.key" type="button" class="status-legend__item" @click="goToDevices({ overview_filter: item.key })">
                <i :style="{ backgroundColor: item.color }" />
                <span>{{ item.label }}</span>
                <strong>{{ item.count }}</strong>
              </button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="18" class="dashboard-row">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="never" v-loading="overviewLoading">
          <template #header>
            <div class="card-title"><span>未来六个月到期趋势</span><small>仅统计当前在保设备</small></div>
          </template>
          <el-empty v-if="!hasTrendData" description="未来六个月暂无到期设备" :image-size="58" />
          <div v-else class="bar-chart" aria-label="未来六个月到期设备数量柱状图">
            <button v-for="item in overview.expiry_trend" :key="item.month" type="button" class="bar-chart__item" @click="goToExpiryMonth(item.month)">
              <span class="bar-chart__value">{{ item.count }}</span>
              <div class="bar-chart__track"><div class="bar-chart__bar" :style="{ height: trendBarHeight(item.count) }" /></div>
              <span class="bar-chart__label">{{ item.label }}</span>
            </button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="chart-card attention-card" shadow="never" v-loading="overviewLoading">
          <template #header>
            <div class="card-title"><span>重点客户关注</span><small>按过保和 30 天内到期排序</small></div>
          </template>
          <el-empty v-if="!overview.attention_customers.length" description="暂无客户设备数据" :image-size="58" />
          <el-table v-else :data="overview.attention_customers" size="small" max-height="260" class="attention-customer-table" @row-click="goToCustomerDevices">
            <el-table-column prop="customer_name" label="客户" min-width="150" show-overflow-tooltip />
            <el-table-column prop="device_count" label="设备" width="65" align="center" />
            <el-table-column prop="in_warranty" label="在保" width="65" align="center" />
            <el-table-column prop="expiring_30" label="30天内" width="75" align="center">
              <template #default="scope"><span class="warning-number">{{ scope.row.expiring_30 }}</span></template>
            </el-table-column>
            <el-table-column prop="expired" label="过保" width="65" align="center">
              <template #default="scope"><span class="danger-number">{{ scope.row.expired }}</span></template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { confirmDashboardReminder, fetchDashboardOverview, fetchDashboardReminders } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'

function emptyOverview() {
  return {
    metrics: { devices_total: 0, in_warranty: 0, expiring_30: 0, expired: 0, customers_total: 0 },
    service_status: [],
    expiry_trend: [],
    attention_customers: [],
  }
}

const overview = ref(emptyOverview())
const router = useRouter()
const overviewLoading = ref(false)
const reminders = ref([])
const loading = ref(false)
const reminderPage = ref(1)
const reminderPageSize = 5
const reminderTypeFilter = ref('all')

const metricCards = computed(() => [
  { key: 'devices', label: '设备总数', value: overview.value.metrics.devices_total, desc: '当前可见设备资产', deviceQuery: {} },
  { key: 'warranty', label: '在保设备', value: overview.value.metrics.in_warranty, desc: '服务周期仍有效', deviceQuery: { overview_filter: 'in_warranty' } },
  { key: 'expiring', label: '30 天内到期', value: overview.value.metrics.expiring_30, desc: '优先跟进续保', deviceQuery: { overview_filter: 'expiring_30' } },
  { key: 'expired', label: '已过保设备', value: overview.value.metrics.expired, desc: '需要评估服务状态', deviceQuery: { overview_filter: 'expired' } },
  { key: 'customers', label: '覆盖客户', value: overview.value.metrics.customers_total, desc: '已关联设备客户', route: '/customers' },
])
const filteredReminders = computed(() => reminders.value.filter((item) => (
  reminderTypeFilter.value === 'all' || item.type === reminderTypeFilter.value
)))
const paginatedReminders = computed(() => filteredReminders.value.slice(
  (reminderPage.value - 1) * reminderPageSize,
  reminderPage.value * reminderPageSize,
))
const statusChartBackground = computed(() => {
  const total = overview.value.metrics.devices_total
  if (!total) return '#edf2f7'
  let current = 0
  const segments = overview.value.service_status
    .filter((item) => item.count > 0)
    .map((item) => {
      const start = current
      current += item.count / total * 100
      return `${item.color} ${start}% ${current}%`
    })
  return `conic-gradient(${segments.join(', ')})`
})
const maxTrendCount = computed(() => Math.max(...overview.value.expiry_trend.map((item) => item.count), 1))
const hasTrendData = computed(() => overview.value.expiry_trend.some((item) => item.count > 0))

async function loadOverview() {
  overviewLoading.value = true
  try {
    const { data } = await fetchDashboardOverview()
    overview.value = { ...emptyOverview(), ...data }
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载设备总览失败'))
  } finally {
    overviewLoading.value = false
  }
}

async function loadReminders() {
  loading.value = true
  try {
    const { data } = await fetchDashboardReminders()
    reminders.value = unwrapList(data)
    reminderPage.value = 1
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载待办提醒失败'))
  } finally {
    loading.value = false
  }
}

async function confirmReminder(reminder) {
  try {
    await confirmDashboardReminder(reminder.key)
    reminders.value = reminders.value.filter((item) => item.key !== reminder.key)
    reminderPage.value = Math.min(reminderPage.value, Math.max(1, Math.ceil(filteredReminders.value.length / reminderPageSize)))
    ElMessage.success('待办已确认并隐藏')
  } catch (error) {
    ElMessage.error(formatApiError(error, '确认待办失败'))
  }
}

function trendBarHeight(count) {
  return `${Math.max(8, Math.round(count / maxTrendCount.value * 100))}%`
}

function handleMetricClick(item) {
  if (item.deviceQuery) {
    goToDevices(item.deviceQuery)
    return
  }
  router.push(item.route)
}

function goToDevices(query = {}) {
  router.push({ path: '/device-center', query })
}

function goToExpiryMonth(month) {
  const [year, monthNumber] = month.split('-').map(Number)
  const nextMonth = monthNumber === 12 ? 1 : monthNumber + 1
  const nextYear = monthNumber === 12 ? year + 1 : year
  goToDevices({
    overview_filter: 'in_warranty',
    service_end_from: `${month}-01`,
    service_end_to: `${nextYear}-${String(nextMonth).padStart(2, '0')}-01`,
  })
}

function goToCustomerDevices(row) {
  goToDevices({ customer_id: row.customer_id })
}

function reminderTypeLabel(type) {
  return type === 'service_expiring' ? '服务即将到期' : '服务任务'
}

function daysLeftLabel(daysLeft) {
  return daysLeft < 0 ? `逾期 ${Math.abs(daysLeft)} 天` : `${daysLeft} 天`
}

onMounted(() => {
  loadOverview()
  loadReminders()
})
</script>

<style scoped>
.dashboard {
  height: 100%;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}

.overview-section {
  margin-bottom: 18px;
}

.section-title,
.card-title,
.todo-card__header,
.todo-card__tools,
.service-chart-content,
.status-legend__item,
.bar-chart {
  display: flex;
}

.section-title,
.todo-card__header,
.card-title {
  align-items: center;
  justify-content: space-between;
}

.section-title h2 {
  margin: 2px 0 0;
  font-size: 22px;
}

.section-title__hint,
.card-title small {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  margin-top: 12px;
}

.metric-card {
  width: 100%;
  min-height: 126px;
  padding: 20px;
  border: 1px solid #e5edf6;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 4px 16px rgb(24 52 82 / 4%);
  cursor: pointer;
  }

.metric-card:hover,
.status-legend__item:hover,
.bar-chart__item:hover {
  border-color: #9fc2ef;
  box-shadow: 0 4px 16px rgb(24 52 82 / 8%);
}

.metric-card span,
.metric-card p {
  color: #718198;
  font-size: 13px;
}

.metric-card strong {
  display: block;
  margin-top: 10px;
  color: #1d3554;
  font-size: 30px;
  line-height: 1;
}

.metric-card p {
  margin: 12px 0 0;
}

.metric-card--expiring { border-top: 3px solid #f2a93b; }
.metric-card--expired { border-top: 3px solid #eb6b6b; }
.metric-card--warranty { border-top: 3px solid #35b7a8; }

.dashboard-row + .dashboard-row {
  margin-top: 18px;
}

.todo-card,
.chart-card {
  height: 100%;
}

.todo-card :deep(.el-card__body) {
  padding-top: 0;
}

.todo-table-scroll {
  max-height: 260px;
  overflow: auto;
}

.todo-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.todo-card__tools {
  align-items: center;
  gap: 12px;
}

.todo-type-filter {
  width: 170px;
}

.service-chart-content {
  align-items: center;
  gap: 22px;
  min-height: 224px;
}

.donut-chart {
  display: grid;
  flex: 0 0 178px;
  width: 178px;
  height: 178px;
  place-items: center;
  border-radius: 50%;
}

.donut-chart__center {
  display: flex;
  width: 122px;
  height: 122px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff;
}

.donut-chart__center strong {
  color: #1d3554;
  font-size: 28px;
}

.donut-chart__center span {
  margin-top: 4px;
  color: #8492a6;
  font-size: 13px;
}

.status-legend {
  min-width: 0;
  flex: 1;
}

.status-legend__item {
  align-items: center;
  width: 100%;
  gap: 8px;
  padding: 6px 0;
  border: 1px solid transparent;
  border-radius: 5px;
  background: transparent;
  color: #65758b;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
}

.status-legend__item i {
  width: 9px;
  height: 9px;
  flex: 0 0 auto;
  border-radius: 50%;
}

.status-legend__item span {
  overflow: hidden;
  flex: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-legend__item strong {
  color: #1d3554;
}

.bar-chart {
  height: 220px;
  align-items: flex-end;
  justify-content: space-around;
  gap: 12px;
  padding: 8px 8px 0;
}

.bar-chart__item {
  display: flex;
  height: 100%;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  align-items: center;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
}

.bar-chart__value {
  height: 24px;
  color: #385473;
  font-size: 13px;
}

.bar-chart__track {
  display: flex;
  width: 100%;
  flex: 1;
  align-items: flex-end;
  justify-content: center;
  border-bottom: 1px solid #dfe7f0;
}

.bar-chart__bar {
  width: min(36px, 68%);
  min-height: 6px;
  border-radius: 6px 6px 0 0;
  background: linear-gradient(180deg, #62a8ff, #347ff0);
}

.bar-chart__label {
  margin-top: 9px;
  color: #7a899d;
  font-size: 12px;
  white-space: nowrap;
}

.attention-card :deep(.el-card__body) {
  padding-top: 2px;
}

.attention-customer-table :deep(.el-table__row) {
  cursor: pointer;
}

.warning-number { color: #d68b00; }
.danger-number { color: #dc4d4d; }

@media (max-width: 1200px) {
  .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .dashboard-row :deep(.el-col + .el-col) { margin-top: 18px; }
}

@media (max-width: 640px) {
  .section-title { align-items: flex-start; gap: 8px; flex-direction: column; }
  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metric-card { min-height: 108px; padding: 16px; }
  .service-chart-content { align-items: flex-start; flex-direction: column; }
  .todo-card__header { align-items: flex-start; gap: 10px; flex-direction: column; }
}
</style>
