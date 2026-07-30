<template>
  <div class="dashboard">
    <el-row :gutter="18">
      <el-col v-for="item in cards" :key="item.title" :xs="24" :sm="12" :lg="6">
        <div class="metric-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.title }}</strong>
          <p>{{ item.desc }}</p>
        </div>
      </el-col>
    </el-row>
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
            <el-table-column prop="content" label="待办内容" min-width="420" />
            <el-table-column prop="target_date" label="日期" width="130" />
            <el-table-column label="剩余" width="100">
              <template #default="scope">{{ daysLeftLabel(scope.row.days_left) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="scope"><el-button link type="primary" @click="confirmReminder(scope.row)">确认</el-button></template>
            </el-table-column>
          </el-table>
        </div>
        <div class="todo-pagination">
          <el-pagination background small layout="total, prev, pager, next" :current-page="reminderPage" :page-size="reminderPageSize" :total="filteredReminders.length" @current-change="reminderPage = $event" />
        </div>
      </template>
    </el-card>
    <el-card class="flow-card" shadow="never">
      <template #header>第一阶段主流程</template>
      <el-steps :active="3" finish-status="success" align-center>
        <el-step title="组织人员" description="客户、厂商、联系人" />
        <el-step title="销售关系" description="销售负责客户" />
        <el-step title="设备资产" description="产品、型号、设备" />
        <el-step title="合同链路" description="参与方与设备绑定" />
      </el-steps>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { confirmDashboardReminder, fetchDashboardReminders } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'

const cards = [
  { label: 'Customer', title: '客户中心', desc: '组织树、联系人、销售、设备、合同' },
  { label: 'Device', title: '设备中心', desc: '设备实例、授权、图片、合同绑定' },
  { label: 'Sales', title: '销售中心', desc: '查看销售负责客户和设备合同' },
  { label: 'Contract', title: '合同中心', desc: '合同参与方链路和采购路径' },
]

const reminders = ref([])
const loading = ref(false)
const reminderPage = ref(1)
const reminderPageSize = 5
const reminderTypeFilter = ref('all')
const filteredReminders = computed(() => reminders.value.filter((item) => (
  reminderTypeFilter.value === 'all' || item.type === reminderTypeFilter.value
)))
const paginatedReminders = computed(() => filteredReminders.value.slice(
  (reminderPage.value - 1) * reminderPageSize,
  reminderPage.value * reminderPageSize,
))

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

function reminderTypeLabel(type) {
  return type === 'service_expiring' ? '服务即将到期' : '服务任务'
}

function daysLeftLabel(daysLeft) {
  return daysLeft < 0 ? `逾期 ${Math.abs(daysLeft)} 天` : `${daysLeft} 天`
}

onMounted(loadReminders)
</script>

<style scoped>
.dashboard {
  height: 100%;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}

.todo-card,
.flow-card {
  margin-top: 18px;
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

.todo-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.todo-card__tools {
  display: flex;
  align-items: center;
  gap: 12px;
}

.todo-type-filter {
  width: 170px;
}
</style>
