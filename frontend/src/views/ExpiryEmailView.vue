<template>
  <div class="page-scroll-layout expiry-page">
    <div class="summary-row">
      <button
        v-for="item in statusCards"
        :key="item.value"
        class="summary-card"
        :class="{ 'is-active': filters.status === item.value }"
        type="button"
        @click="selectStatus(item.value)"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.count }}</strong>
      </button>
    </div>

    <el-alert
      v-if="!emailConfigured"
      class="mb-16"
      title="发件邮箱尚未配置，当前只能查看到期清单，不能发送邮件。"
      type="warning"
      :closable="false"
      show-icon
    />
    <el-alert
      v-else
      class="mb-16"
      :title="emailStatusTitle"
      type="success"
      :closable="false"
      show-icon
    />

    <div class="toolbar">
      <el-input
        v-model="filters.search"
        clearable
        placeholder="搜索客户、项目、设备、序列号或销售"
        @keyup.enter="search"
        @clear="search"
      />
      <div class="action-row">
        <el-button @click="search">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
        <el-button v-if="canUpdateSettings" @click="openCcSettings">统一抄送配置</el-button>
        <el-button type="primary" :loading="batchSending" :disabled="!emailConfigured || !sendableCount" @click="sendAll">
          一键汇总发送（{{ sendableCount }} 台设备）
        </el-button>
        <el-button :loading="batchResending" :disabled="!emailConfigured || !statistics.sent" @click="resendAllSent">
          一键重发已发送（{{ statistics.sent }} 台设备）
        </el-button>
      </div>
    </div>

    <div class="page-table-scroll">
      <el-table v-loading="loading" :data="rows" height="100%">
        <el-table-column prop="customer_name" label="客户" min-width="150" show-overflow-tooltip />
        <el-table-column label="项目" min-width="190" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="primary-cell">{{ row.project_name || '-' }}</div>
            <small>{{ row.project_no || '-' }}</small>
          </template>
        </el-table-column>
        <el-table-column label="设备" min-width="190" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="primary-cell">{{ row.device_model || row.device_name || '-' }}</div>
            <small>SN：{{ row.serial_number || '-' }}</small>
          </template>
        </el-table-column>
        <el-table-column label="负责销售" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="primary-cell">{{ row.sales_name || '未绑定销售' }}</div>
            <small :class="{ 'missing-email': !row.sales_email }">{{ row.sales_email || '未维护邮箱' }}</small>
          </template>
        </el-table-column>
        <el-table-column prop="service_end_date" label="维保到期日" width="125" />
        <el-table-column label="剩余时间" width="105">
          <template #default="{ row }">
            <el-tag :type="row.days_left <= 30 ? 'danger' : row.days_left <= 90 ? 'warning' : 'info'" effect="plain">
              {{ row.days_left }} 天
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发送状态" width="115">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.delivery_status]?.type || 'info'">
              {{ statusMeta[row.delivery_status]?.label || row.delivery_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发送结果" min-width="175" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.sent_at">{{ formatDateTime(row.sent_at) }}</span>
            <span v-else-if="row.last_error" class="error-text">{{ row.last_error }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="95" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              :loading="sendingIds.has(row.project_device_id)"
              :disabled="!emailConfigured || !row.can_send"
              @click="sendOne(row)"
            >
              {{ row.delivery_status === 'sent' ? '重新发送' : row.delivery_status === 'failed' ? '重试' : '发送' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-row">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadRows"
        @size-change="handleSizeChange"
      />
    </div>

    <el-dialog v-model="ccDialogVisible" title="统一抄送配置" width="560px">
      <el-alert
        title="所有维保提醒邮件都会在发送给负责销售的同时，抄送到以下邮箱。输入邮箱后按回车添加。"
        type="info"
        :closable="false"
        show-icon
        class="mb-16"
      />
      <el-form label-position="top">
        <el-form-item label="统一抄送邮箱">
          <el-select
            v-model="ccForm"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入邮箱并按回车，可添加多个"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ccDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="ccSaving" @click="saveCcSettings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchExpiryEmailReminders, fetchExpiryEmailSettings, saveExpiryEmailSettings, sendExpiryEmailReminders } from '../api/resources'
import { formatApiError } from '../utils/apiData'

const loading = ref(false)
const batchSending = ref(false)
const batchResending = ref(false)
const sendingIds = ref(new Set())
const rows = ref([])
const emailConfigured = ref(false)
const sender = ref('')
const ccEmails = ref([])
const canUpdateSettings = ref(false)
const ccDialogVisible = ref(false)
const ccSaving = ref(false)
const ccForm = ref([])
const statistics = reactive({ all: 0, pending: 0, failed: 0, sent: 0 })
const filters = reactive({ status: '', search: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const statusMeta = {
  pending: { label: '待发送', type: 'warning' },
  sending: { label: '发送中', type: 'info' },
  sent: { label: '已发送', type: 'success' },
  failed: { label: '发送失败', type: 'danger' },
}

const statusCards = computed(() => [
  { label: '全部即将到期', value: '', count: statistics.all },
  { label: '待发送', value: 'pending', count: statistics.pending },
  { label: '发送失败', value: 'failed', count: statistics.failed },
  { label: '已发送', value: 'sent', count: statistics.sent },
])
const sendableCount = computed(() => statistics.pending + statistics.failed)
const emailStatusTitle = computed(() => {
  const ccText = ccEmails.value.length ? `统一抄送：${ccEmails.value.join('、')}` : '当前未配置统一抄送'
  return `邮件将通过 ${sender.value} 发送；${ccText}。同一设备的同一维保周期只会自动发送一次。`
})

async function loadRows() {
  loading.value = true
  try {
    const { data } = await fetchExpiryEmailReminders({
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filters.status || undefined,
      search: filters.search.trim() || undefined,
    })
    rows.value = data.results || []
    pagination.total = data.count || 0
    Object.assign(statistics, data.statistics || {})
    emailConfigured.value = Boolean(data.email_configured)
    sender.value = data.sender || ''
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载维保邮件清单失败'))
  } finally {
    loading.value = false
  }
}

async function loadSettings() {
  try {
    const { data } = await fetchExpiryEmailSettings()
    ccEmails.value = data.cc_emails || []
    canUpdateSettings.value = Boolean(data.can_update)
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载统一抄送配置失败'))
  }
}

function openCcSettings() {
  ccForm.value = [...ccEmails.value]
  ccDialogVisible.value = true
}

async function saveCcSettings() {
  ccSaving.value = true
  try {
    const { data } = await saveExpiryEmailSettings(ccForm.value)
    ccEmails.value = data.cc_emails || []
    ccDialogVisible.value = false
    ElMessage.success('统一抄送配置已保存')
  } catch (error) {
    ElMessage.error(formatApiError(error, '保存统一抄送配置失败'))
  } finally {
    ccSaving.value = false
  }
}

function selectStatus(status) {
  filters.status = status
  pagination.page = 1
  loadRows()
}

function search() {
  pagination.page = 1
  loadRows()
}

function resetFilters() {
  filters.status = ''
  filters.search = ''
  pagination.page = 1
  loadRows()
}

function handleSizeChange() {
  pagination.page = 1
  loadRows()
}

async function sendAll() {
  await ElMessageBox.confirm(`将按负责销售汇总 ${sendableCount.value} 台设备，同一销售只收到一封汇总邮件；已发送过的设备会自动跳过。是否继续？`, '发送确认', { type: 'warning' })
  batchSending.value = true
  try {
    const { data } = await sendExpiryEmailReminders()
    ElMessage.success(`发送完成：共发出 ${data.emails_sent} 封邮件，覆盖 ${data.sent} 台设备；失败 ${data.failed} 台，跳过 ${data.skipped} 台`)
    await loadRows()
  } catch (error) {
    ElMessage.error(formatApiError(error, '批量发送失败'))
  } finally {
    batchSending.value = false
  }
}

async function resendAllSent() {
  await ElMessageBox.confirm(`将把 ${statistics.sent} 台已发送设备按负责销售重新汇总，同一销售收到一封新邮件。是否继续？`, '批量重发确认', { type: 'warning' })
  batchResending.value = true
  try {
    const { data } = await sendExpiryEmailReminders(null, true, true)
    ElMessage.success(`重发完成：共发出 ${data.emails_sent} 封邮件，覆盖 ${data.sent} 台设备；失败 ${data.failed} 台`)
    await loadRows()
  } catch (error) {
    ElMessage.error(formatApiError(error, '批量重新发送失败'))
  } finally {
    batchResending.value = false
  }
}

async function sendOne(row) {
  const forceResend = row.delivery_status === 'sent'
  if (forceResend) {
    await ElMessageBox.confirm(`该设备已于 ${formatDateTime(row.sent_at)} 发送过提醒，确定再次发送给 ${row.sales_email}？`, '重新发送确认', { type: 'warning' })
  }
  const next = new Set(sendingIds.value)
  next.add(row.project_device_id)
  sendingIds.value = next
  try {
    const { data } = await sendExpiryEmailReminders([row.project_device_id], forceResend)
    if (data.sent) ElMessage.success(`${forceResend ? '提醒邮件已重新发送' : '提醒邮件已发送'}至 ${row.sales_email}`)
    else if (data.failed) ElMessage.error(data.results?.[0]?.error || '发送失败')
    else ElMessage.info('该维保周期已发送过，无需重复发送')
    await loadRows()
  } catch (error) {
    ElMessage.error(formatApiError(error, '发送邮件失败'))
  } finally {
    const updated = new Set(sendingIds.value)
    updated.delete(row.project_device_id)
    sendingIds.value = updated
  }
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'
}

onMounted(() => Promise.all([loadRows(), loadSettings()]))
</script>

<style scoped>
.expiry-page { gap: 0; }
.summary-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.summary-card { display: flex; min-height: 68px; padding: 14px 16px; align-items: center; justify-content: space-between; border: 1px solid var(--app-border); border-radius: var(--app-radius-lg); background: var(--app-surface); color: var(--app-text); cursor: pointer; }
.summary-card strong { color: var(--app-ink); font-size: 24px; }
.summary-card.is-active { border-color: var(--app-primary); background: var(--app-primary-soft); color: var(--app-primary); }
.toolbar { display: grid; grid-template-columns: minmax(280px, 1fr) auto; gap: 12px; margin-bottom: 14px; }
.primary-cell { color: var(--app-ink); }
small { color: var(--app-subtle); }
.missing-email, .error-text { color: var(--app-danger); }
.pagination-row { display: flex; justify-content: flex-end; padding-top: 14px; }
@media (max-width: 900px) {
  .summary-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .toolbar { grid-template-columns: 1fr; }
}
</style>
