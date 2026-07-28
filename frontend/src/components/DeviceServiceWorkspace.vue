<template>
  <el-tabs v-model="activeTab">
    <el-tab-pane label="服务计划" name="plans">
      <div class="service-actions">
        <el-button v-if="!plans.length" type="primary" @click="openPlanDialog">配置服务计划</el-button>
        <el-button v-else type="primary" @click="openScheduleDialog">新增服务项</el-button>
      </div>
      <el-empty v-if="!plans.length" description="当前设备暂无服务计划" :image-size="64" />
      <template v-else>
        <el-table :data="plans" stripe>
          <el-table-column label="服务项目" min-width="180"><template #default="scope">{{ scope.row.project_device_detail?.project_name || '-' }}</template></el-table-column>
          <el-table-column label="巡检频率" min-width="120"><template #default="scope">{{ frequencyLabel(scope.row.inspection_frequency) }}</template></el-table-column>
          <el-table-column prop="first_inspection_date" label="首次巡检" min-width="120" />
          <el-table-column prop="reminder_days" label="提前提醒（天）" min-width="130" />
          <el-table-column label="服务内容" min-width="180"><template #default="scope">{{ contentsLabel(scope.row.service_contents) }}</template></el-table-column>
        </el-table>
        <el-table v-if="schedules.length" :data="schedules" stripe class="mt-16">
          <el-table-column label="服务项" min-width="130"><template #default="scope">{{ operationRecordTypeLabel(scope.row.service_type) }}</template></el-table-column>
          <el-table-column label="执行频率" min-width="130"><template #default="scope">{{ frequencyLabel(scope.row.frequency) }}</template></el-table-column>
          <el-table-column prop="first_service_date" label="首次执行" min-width="130" />
          <el-table-column prop="reminder_days" label="提前提醒（天）" min-width="130" />
        </el-table>
      </template>
    </el-tab-pane>
    <el-tab-pane :label="`服务任务（${tasks.length}）`" name="tasks">
      <el-empty v-if="!tasks.length" description="暂无服务任务" :image-size="64" />
      <el-table v-else :data="tasks" stripe>
        <el-table-column label="任务类型" min-width="110"><template #default="scope">{{ operationRecordTypeLabel(scope.row.task_type) }}</template></el-table-column>
        <el-table-column prop="planned_date" label="计划日期" min-width="140" />
        <el-table-column label="状态" min-width="110"><template #default="scope">{{ taskStatusLabel(scope.row.status) }}</template></el-table-column>
        <el-table-column prop="reminder_date" label="提醒日期" min-width="130" />
        <el-table-column prop="completed_at" label="完成时间" min-width="180" />
      </el-table>
    </el-tab-pane>
    <el-tab-pane :label="`运维记录（${records.length}）`" name="records">
      <div class="service-actions"><el-button type="primary" @click="openRecordDialog">新增运维记录</el-button></div>
      <el-empty v-if="!records.length" description="暂无运维记录" :image-size="64" />
      <el-table v-else :data="records" stripe>
        <el-table-column label="类型" min-width="120"><template #default="scope">{{ operationRecordTypeLabel(scope.row.record_type) }}</template></el-table-column>
        <el-table-column prop="performed_at" label="服务时间" min-width="180" />
        <el-table-column prop="result" label="结论" min-width="110" />
        <el-table-column prop="issue_description" label="问题描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="resolution" label="处理措施" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-tab-pane>
  </el-tabs>

  <el-dialog v-model="planDialogVisible" title="配置设备服务计划" width="620px" append-to-body>
    <el-form label-width="120px">
      <el-form-item v-if="!projectDeviceId" label="项目服务周期" required><el-select v-model="planForm.projectDeviceId" class="form-control"><el-option v-for="item in projectDevices" :key="item.id" :label="`${item.project_name || item.project_device_detail?.project_name || '项目'}（${item.service_start_date || '-'} 至 ${item.service_end_date || '-'}）`" :value="item.id" /></el-select></el-form-item>
      <el-form-item label="首次巡检日期"><el-date-picker v-model="planForm.firstInspectionDate" type="date" value-format="YYYY-MM-DD" class="form-control" /></el-form-item>
      <el-form-item label="巡检频率" required><el-select v-model="planForm.frequency" class="form-control"><el-option label="每月" value="monthly" /><el-option label="每季度" value="quarterly" /><el-option label="每半年" value="semiannual" /><el-option label="每年" value="annual" /><el-option label="自定义天数" value="custom" /></el-select></el-form-item>
      <el-form-item v-if="planForm.frequency === 'custom'" label="巡检间隔" required><el-input-number v-model="planForm.intervalDays" :min="1" /></el-form-item>
      <el-form-item label="提前提醒"><el-input-number v-model="planForm.reminderDays" :min="0" /></el-form-item>
      <el-form-item label="服务内容"><el-checkbox-group v-model="planForm.contents"><el-checkbox label="inspection">巡检</el-checkbox><el-checkbox label="system_upgrade">系统升级</el-checkbox><el-checkbox label="rule_library_upgrade">规则库升级</el-checkbox><el-checkbox label="technical_support">技术支持</el-checkbox></el-checkbox-group></el-form-item>
    </el-form>
    <template #footer><el-button @click="planDialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="savePlan">保存并生成服务任务</el-button></template>
  </el-dialog>

  <el-dialog v-model="scheduleDialogVisible" title="新增服务项计划" width="560px" append-to-body>
    <el-form label-width="110px">
      <el-form-item label="服务项" required><el-select v-model="scheduleForm.serviceType" class="form-control"><el-option label="巡检" value="inspection" /><el-option label="系统升级" value="system_upgrade" /><el-option label="规则库升级" value="rule_library_upgrade" /></el-select></el-form-item>
      <el-form-item label="首次执行日期"><el-date-picker v-model="scheduleForm.firstDate" type="date" value-format="YYYY-MM-DD" class="form-control" /></el-form-item>
      <el-form-item label="执行频率" required><el-select v-model="scheduleForm.frequency" class="form-control"><el-option label="每月" value="monthly" /><el-option label="每季度" value="quarterly" /><el-option label="每半年" value="semiannual" /><el-option label="每年" value="annual" /><el-option label="自定义天数" value="custom" /></el-select></el-form-item>
      <el-form-item v-if="scheduleForm.frequency === 'custom'" label="执行间隔" required><el-input-number v-model="scheduleForm.intervalDays" :min="1" /></el-form-item>
      <el-form-item label="提前提醒"><el-input-number v-model="scheduleForm.reminderDays" :min="0" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="scheduleDialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveSchedule">保存并生成任务</el-button></template>
  </el-dialog>

  <el-dialog v-model="recordDialogVisible" title="新增设备运维记录" width="680px" append-to-body>
    <el-form label-width="110px">
      <el-form-item label="服务计划" required><el-select v-model="recordForm.planId" class="form-control" @change="syncRecordBinding"><el-option v-for="item in plans" :key="item.id" :label="item.project_device_detail?.project_name || `服务计划 #${item.id}`" :value="item.id" /></el-select></el-form-item>
      <el-form-item label="服务类型" required><el-select v-model="recordForm.type" class="form-control"><el-option label="巡检" value="inspection" /><el-option label="系统升级" value="system_upgrade" /><el-option label="规则库升级" value="rule_library_upgrade" /><el-option label="故障处理" value="fault_handling" /><el-option label="配置变更" value="configuration_change" /><el-option label="技术支持" value="technical_support" /></el-select></el-form-item>
      <el-form-item v-if="['inspection','system_upgrade','rule_library_upgrade'].includes(recordForm.type)" label="关联服务任务"><el-select v-model="recordForm.taskId" clearable class="form-control"><el-option v-for="item in availableTasks" :key="item.id" :label="`${item.planned_date}（${taskStatusLabel(item.status)}）`" :value="item.id" /></el-select></el-form-item>
      <el-form-item label="服务时间" required><el-date-picker v-model="recordForm.performedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" class="form-control" /></el-form-item>
      <el-form-item label="处理结论"><el-select v-model="recordForm.result" class="form-control"><el-option label="正常" value="normal" /><el-option label="发现问题" value="issue_found" /><el-option label="需跟进" value="follow_up" /></el-select></el-form-item>
      <el-form-item label="问题描述"><el-input v-model="recordForm.issue" type="textarea" :rows="2" /></el-form-item>
      <el-form-item label="处理措施"><el-input v-model="recordForm.resolution" type="textarea" :rows="2" /></el-form-item>
      <el-form-item label="升级后系统版本"><el-input v-model="recordForm.softwareVersion" /></el-form-item>
      <el-form-item label="升级后规则库版本"><el-input v-model="recordForm.ruleLibraryVersion" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="recordDialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveRecord">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createResource, listAllResource } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'
import { INSPECTION_TASK_STATUS_LABELS, OPERATION_RECORD_TYPE_LABELS } from '../utils/displayMaps'

const props = defineProps({ deviceId: { type: Number, required: true }, projectDeviceId: { type: Number, default: null }, projectDevices: { type: Array, default: () => [] } })
const activeTab = ref('plans')
const plans = ref([]); const schedules = ref([]); const tasks = ref([]); const records = ref([])
const planDialogVisible = ref(false); const scheduleDialogVisible = ref(false); const recordDialogVisible = ref(false); const saving = ref(false)
const planForm = reactive({ projectDeviceId: null, firstInspectionDate: '', frequency: 'quarterly', intervalDays: null, reminderDays: 7, contents: ['inspection'] })
const scheduleForm = reactive({ serviceType: 'system_upgrade', firstDate: '', frequency: 'semiannual', intervalDays: null, reminderDays: 7 })
const recordForm = reactive({ planId: null, projectDeviceId: null, taskId: null, type: 'inspection', performedAt: '', result: 'normal', issue: '', resolution: '', softwareVersion: '', ruleLibraryVersion: '' })
const availableTasks = computed(() => tasks.value.filter((task) => task.service_plan === recordForm.planId && task.task_type === recordForm.type && !['completed', 'cancelled'].includes(task.status)))
const frequencyLabel = (value) => ({ monthly: '每月', quarterly: '每季度', semiannual: '每半年', annual: '每年', custom: '自定义天数' })[value] || value || '-'
const taskStatusLabel = (value) => INSPECTION_TASK_STATUS_LABELS[value] || value || '-'
const operationRecordTypeLabel = (value) => OPERATION_RECORD_TYPE_LABELS[value] || value || '-'
const contentsLabel = (values) => Array.isArray(values) && values.length ? values.map((item) => operationRecordTypeLabel(item)).join('、') : '-'

async function load() {
  if (!props.deviceId) return
  const planParams = props.projectDeviceId ? { project_device: props.projectDeviceId } : { device: props.deviceId }
  const [plansResponse, tasksResponse, recordsResponse] = await Promise.all([listAllResource('device-service-plans', planParams), listAllResource('inspection-tasks', { device: props.deviceId }), listAllResource('device-operation-records', { device: props.deviceId })])
  plans.value = unwrapList(plansResponse.data)
  const planIds = new Set(plans.value.map((item) => item.id))
  tasks.value = unwrapList(tasksResponse.data).filter((item) => planIds.has(item.service_plan))
  records.value = unwrapList(recordsResponse.data).filter((item) => planIds.has(item.service_plan))
  const scheduleResponses = await Promise.all(plans.value.map((plan) => listAllResource('device-service-schedules', { service_plan: plan.id })))
  schedules.value = scheduleResponses.flatMap((response) => unwrapList(response.data))
}
watch(() => [props.deviceId, props.projectDeviceId], () => load().catch((error) => ElMessage.error(formatApiError(error, '加载设备服务失败'))), { immediate: true })

function openPlanDialog() { if (!props.projectDeviceId && !props.projectDevices.length) return ElMessage.warning('当前设备尚未绑定项目服务周期'); Object.assign(planForm, { projectDeviceId: props.projectDeviceId || props.projectDevices[0]?.id || null, firstInspectionDate: '', frequency: 'quarterly', intervalDays: null, reminderDays: 7, contents: ['inspection'] }); planDialogVisible.value = true }
async function savePlan() { if (!planForm.projectDeviceId) return ElMessage.warning('请选择项目服务周期'); if (planForm.frequency === 'custom' && !planForm.intervalDays) return ElMessage.warning('请填写自定义巡检间隔天数'); saving.value = true; try { await createResource('device-service-plans', { project_device: planForm.projectDeviceId, inspection_frequency: planForm.frequency, ...(planForm.firstInspectionDate ? { first_inspection_date: planForm.firstInspectionDate } : {}), ...(planForm.frequency === 'custom' ? { inspection_interval_days: planForm.intervalDays } : {}), reminder_days: planForm.reminderDays, service_contents: planForm.contents }); planDialogVisible.value = false; ElMessage.success('服务计划已保存，任务已生成'); await load() } catch (error) { ElMessage.error(formatApiError(error, '保存服务计划失败')) } finally { saving.value = false } }
function openScheduleDialog() { Object.assign(scheduleForm, { serviceType: 'system_upgrade', firstDate: '', frequency: 'semiannual', intervalDays: null, reminderDays: 7 }); scheduleDialogVisible.value = true }
async function saveSchedule() { const plan = plans.value[0]; if (!plan) return; if (scheduleForm.frequency === 'custom' && !scheduleForm.intervalDays) return ElMessage.warning('请填写自定义执行间隔天数'); saving.value = true; try { await createResource('device-service-schedules', { service_plan: plan.id, service_type: scheduleForm.serviceType, frequency: scheduleForm.frequency, ...(scheduleForm.firstDate ? { first_service_date: scheduleForm.firstDate } : {}), ...(scheduleForm.frequency === 'custom' ? { interval_days: scheduleForm.intervalDays } : {}), reminder_days: scheduleForm.reminderDays }); scheduleDialogVisible.value = false; ElMessage.success('服务项计划已保存，任务已生成'); await load() } catch (error) { ElMessage.error(formatApiError(error, '保存服务项计划失败')) } finally { saving.value = false } }
function openRecordDialog() { if (!plans.value.length) return ElMessage.warning('请先配置服务计划'); Object.assign(recordForm, { planId: plans.value[0].id, projectDeviceId: plans.value[0].project_device, taskId: null, type: 'inspection', performedAt: new Date().toISOString().slice(0, 19), result: 'normal', issue: '', resolution: '', softwareVersion: '', ruleLibraryVersion: '' }); recordDialogVisible.value = true }
function syncRecordBinding(planId) { const plan = plans.value.find((item) => item.id === planId); recordForm.projectDeviceId = plan?.project_device || null; recordForm.taskId = null }
async function saveRecord() { if (!recordForm.planId || !recordForm.projectDeviceId || !recordForm.performedAt) return ElMessage.warning('请填写服务计划和服务时间'); saving.value = true; try { await createResource('device-operation-records', { device: props.deviceId, project_device: recordForm.projectDeviceId, service_plan: recordForm.planId, record_type: recordForm.type, performed_at: recordForm.performedAt, result: recordForm.result, issue_description: recordForm.issue, resolution: recordForm.resolution, software_version_after: recordForm.softwareVersion, rule_library_version_after: recordForm.ruleLibraryVersion, ...(recordForm.taskId ? { inspection_task: recordForm.taskId } : {}) }); recordDialogVisible.value = false; ElMessage.success('运维记录已保存'); await load() } catch (error) { ElMessage.error(formatApiError(error, '保存运维记录失败')) } finally { saving.value = false } }
</script>

<style scoped>
.service-actions { display: flex; justify-content: flex-end; margin: 0 0 12px; }
.form-control { width: 100%; }
</style>
