<template>
  <el-tabs v-model="activeTab">
    <el-tab-pane label="服务计划" name="plans">
      <div class="service-actions">
        <el-button v-if="!plans.length" type="primary" @click="openPlanDialog">配置服务计划</el-button>
        <el-button v-else type="primary" @click="openScheduleDialog">新增服务项</el-button>
      </div>
      <el-empty v-if="!plans.length" description="当前设备暂无服务计划" :image-size="64" />
      <el-table v-else-if="schedules.length" :data="schedules" stripe>
        <el-table-column label="服务项" min-width="130"><template #default="scope">{{ operationRecordTypeLabel(scope.row.service_type) }}</template></el-table-column>
        <el-table-column label="执行频率" min-width="130"><template #default="scope">{{ frequencyLabel(scope.row.frequency) }}</template></el-table-column>
        <el-table-column prop="first_service_date" label="首次执行" min-width="130" />
        <el-table-column prop="reminder_days" label="提前提醒（天）" min-width="130" />
        <el-table-column label="操作" width="130"><template #default="scope"><el-button link type="primary" @click="openScheduleDialog(scope.row)">编辑</el-button><el-button link type="danger" @click="removeSchedule(scope.row)">删除</el-button></template></el-table-column>
      </el-table>
      <el-empty v-else description="当前服务计划暂无服务项，请新增服务项" :image-size="64" />
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
        <el-table-column label="操作" width="130"><template #default="scope"><el-button link type="primary" @click="openRecordDialog(scope.row)">编辑</el-button><el-button link type="danger" @click="removeRecord(scope.row)">删除</el-button></template></el-table-column>
      </el-table>
    </el-tab-pane>
  </el-tabs>

  <el-dialog v-model="planDialogVisible" :title="editingPlanId ? '编辑设备服务计划' : '配置设备服务计划'" width="620px" append-to-body>
    <el-form label-width="120px">
      <el-form-item v-if="!projectDeviceId" label="项目服务周期" required><el-select v-model="planForm.projectDeviceId" :disabled="Boolean(editingPlanId)" class="form-control"><el-option v-for="item in projectDevices" :key="item.id" :label="`${item.project_name || item.project_device_detail?.project_name || '项目'}（${item.service_start_date || '-'} 至 ${item.service_end_date || '-'}）`" :value="item.id" /></el-select></el-form-item>
      <el-form-item label="首次巡检日期"><el-date-picker v-model="planForm.firstInspectionDate" type="date" value-format="YYYY-MM-DD" class="form-control" /></el-form-item>
      <el-form-item label="巡检频率" required><el-select v-model="planForm.frequency" class="form-control"><el-option label="每月" value="monthly" /><el-option label="每季度" value="quarterly" /><el-option label="每半年" value="semiannual" /><el-option label="每年" value="annual" /><el-option label="自定义天数" value="custom" /></el-select></el-form-item>
      <el-form-item v-if="planForm.frequency === 'custom'" label="巡检间隔" required><el-input-number v-model="planForm.intervalDays" :min="1" /></el-form-item>
      <el-form-item label="提前提醒"><el-input-number v-model="planForm.reminderDays" :min="0" /></el-form-item>
      <el-form-item label="服务内容"><el-checkbox-group v-model="planForm.contents"><el-checkbox label="inspection">巡检</el-checkbox><el-checkbox label="system_upgrade">系统升级</el-checkbox><el-checkbox label="rule_library_upgrade">规则库升级</el-checkbox><el-checkbox label="technical_support">技术支持</el-checkbox></el-checkbox-group></el-form-item>
    </el-form>
    <template #footer><el-button @click="planDialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="savePlan">保存并生成服务任务</el-button></template>
  </el-dialog>

  <el-dialog v-model="scheduleDialogVisible" :title="editingScheduleId ? '编辑服务项计划' : '新增服务项计划'" width="560px" append-to-body>
    <el-form label-width="110px">
      <el-form-item label="服务计划" required><el-select v-model="scheduleForm.planId" :disabled="Boolean(editingScheduleId)" class="form-control"><el-option v-for="item in plans" :key="item.id" :label="item.project_device_detail?.project_name || `服务计划 #${item.id}`" :value="item.id" /></el-select></el-form-item>
      <el-form-item label="服务项" required><el-select v-model="scheduleForm.serviceType" class="form-control"><el-option label="巡检" value="inspection" /><el-option label="系统升级" value="system_upgrade" /><el-option label="规则库升级" value="rule_library_upgrade" /></el-select></el-form-item>
      <el-form-item label="首次执行日期"><el-date-picker v-model="scheduleForm.firstDate" type="date" value-format="YYYY-MM-DD" class="form-control" /></el-form-item>
      <el-form-item label="执行频率" required><el-select v-model="scheduleForm.frequency" class="form-control"><el-option label="每月" value="monthly" /><el-option label="每季度" value="quarterly" /><el-option label="每半年" value="semiannual" /><el-option label="每年" value="annual" /><el-option label="自定义天数" value="custom" /></el-select></el-form-item>
      <el-form-item v-if="scheduleForm.frequency === 'custom'" label="执行间隔" required><el-input-number v-model="scheduleForm.intervalDays" :min="1" /></el-form-item>
      <el-form-item label="提前提醒"><el-input-number v-model="scheduleForm.reminderDays" :min="0" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="scheduleDialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveSchedule">保存并生成任务</el-button></template>
  </el-dialog>

  <el-dialog v-model="recordDialogVisible" :title="editingRecordId ? '编辑设备运维记录' : '新增设备运维记录'" width="680px" append-to-body>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { createResource, deleteResource, listAllResource, updateResource } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'
import { INSPECTION_TASK_STATUS_LABELS, OPERATION_RECORD_TYPE_LABELS } from '../utils/displayMaps'

const props = defineProps({ deviceId: { type: Number, required: true }, projectDeviceId: { type: Number, default: null }, projectDevices: { type: Array, default: () => [] } })
const activeTab = ref('plans')
const plans = ref([]); const schedules = ref([]); const tasks = ref([]); const records = ref([])
const planDialogVisible = ref(false); const scheduleDialogVisible = ref(false); const recordDialogVisible = ref(false); const saving = ref(false)
const editingPlanId = ref(null); const editingScheduleId = ref(null); const editingRecordId = ref(null)
const planForm = reactive({ projectDeviceId: null, firstInspectionDate: '', frequency: 'quarterly', intervalDays: null, reminderDays: 7, contents: ['inspection'] })
const scheduleForm = reactive({ planId: null, serviceType: 'system_upgrade', firstDate: '', frequency: 'semiannual', intervalDays: null, reminderDays: 7 })
const recordForm = reactive({ planId: null, projectDeviceId: null, taskId: null, type: 'inspection', performedAt: '', result: 'normal', issue: '', resolution: '', softwareVersion: '', ruleLibraryVersion: '' })
const availableTasks = computed(() => tasks.value.filter((task) => task.service_plan === recordForm.planId && task.task_type === recordForm.type && !['completed', 'cancelled'].includes(task.status)))
const frequencyLabel = (value) => ({ monthly: '每月', quarterly: '每季度', semiannual: '每半年', annual: '每年', custom: '自定义天数' })[value] || value || '-'
const taskStatusLabel = (value) => INSPECTION_TASK_STATUS_LABELS[value] || value || '-'
const operationRecordTypeLabel = (value) => OPERATION_RECORD_TYPE_LABELS[value] || value || '-'

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

function openPlanDialog(plan = null) { if (!plan && !props.projectDeviceId && !props.projectDevices.length) return ElMessage.warning('当前设备尚未绑定项目服务周期'); editingPlanId.value = plan?.id || null; Object.assign(planForm, { projectDeviceId: plan?.project_device || props.projectDeviceId || props.projectDevices[0]?.id || null, firstInspectionDate: plan?.first_inspection_date || '', frequency: plan?.inspection_frequency || 'quarterly', intervalDays: plan?.inspection_interval_days || null, reminderDays: plan?.reminder_days ?? 7, contents: plan?.service_contents || ['inspection'] }); planDialogVisible.value = true }
async function savePlan() { if (!planForm.projectDeviceId) return ElMessage.warning('请选择项目服务周期'); if (planForm.frequency === 'custom' && !planForm.intervalDays) return ElMessage.warning('请填写自定义巡检间隔天数'); saving.value = true; try { const payload = { project_device: planForm.projectDeviceId, inspection_frequency: planForm.frequency, first_inspection_date: planForm.firstInspectionDate || null, inspection_interval_days: planForm.frequency === 'custom' ? planForm.intervalDays : null, reminder_days: planForm.reminderDays, service_contents: planForm.contents }; if (editingPlanId.value) await updateResource('device-service-plans', editingPlanId.value, payload); else await createResource('device-service-plans', payload); planDialogVisible.value = false; ElMessage.success(editingPlanId.value ? '服务计划已更新' : '服务计划已保存，任务已生成'); await load() } catch (error) { ElMessage.error(formatApiError(error, '保存服务计划失败')) } finally { saving.value = false } }
function openScheduleDialog(schedule = null) { editingScheduleId.value = schedule?.id || null; Object.assign(scheduleForm, { planId: schedule?.service_plan || plans.value[0]?.id || null, serviceType: schedule?.service_type || 'system_upgrade', firstDate: schedule?.first_service_date || '', frequency: schedule?.frequency || 'semiannual', intervalDays: schedule?.interval_days || null, reminderDays: schedule?.reminder_days ?? 7 }); scheduleDialogVisible.value = true }
async function saveSchedule() { if (!scheduleForm.planId) return ElMessage.warning('请选择服务计划'); if (scheduleForm.frequency === 'custom' && !scheduleForm.intervalDays) return ElMessage.warning('请填写自定义执行间隔天数'); saving.value = true; try { const payload = { service_plan: scheduleForm.planId, service_type: scheduleForm.serviceType, frequency: scheduleForm.frequency, first_service_date: scheduleForm.firstDate || null, interval_days: scheduleForm.frequency === 'custom' ? scheduleForm.intervalDays : null, reminder_days: scheduleForm.reminderDays }; if (editingScheduleId.value) await updateResource('device-service-schedules', editingScheduleId.value, payload); else await createResource('device-service-schedules', payload); scheduleDialogVisible.value = false; ElMessage.success(editingScheduleId.value ? '服务项计划已更新' : '服务项计划已保存，任务已生成'); await load() } catch (error) { ElMessage.error(formatApiError(error, '保存服务项计划失败')) } finally { saving.value = false } }
async function removeSchedule(schedule) { try { await ElMessageBox.confirm('删除服务项会一并隐藏其未完成任务，确认继续？', '删除确认', { type: 'warning' }); await deleteResource('device-service-schedules', schedule.id); ElMessage.success('服务项已删除'); await load() } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(formatApiError(error, '删除服务项失败')) } }
function openRecordDialog(record = null) { if (!record && !plans.value.length) return ElMessage.warning('请先配置服务计划'); editingRecordId.value = record?.id || null; Object.assign(recordForm, { planId: record?.service_plan || plans.value[0]?.id || null, projectDeviceId: record?.project_device || plans.value[0]?.project_device || null, taskId: record?.inspection_task || null, type: record?.record_type || 'inspection', performedAt: record?.performed_at || new Date().toISOString().slice(0, 19), result: record?.result || 'normal', issue: record?.issue_description || '', resolution: record?.resolution || '', softwareVersion: record?.software_version_after || '', ruleLibraryVersion: record?.rule_library_version_after || '' }); recordDialogVisible.value = true }
function syncRecordBinding(planId) { const plan = plans.value.find((item) => item.id === planId); recordForm.projectDeviceId = plan?.project_device || null; recordForm.taskId = null }
async function saveRecord() { if (!recordForm.planId || !recordForm.projectDeviceId || !recordForm.performedAt) return ElMessage.warning('请填写服务计划和服务时间'); saving.value = true; try { const payload = { device: props.deviceId, project_device: recordForm.projectDeviceId, service_plan: recordForm.planId, record_type: recordForm.type, performed_at: recordForm.performedAt, result: recordForm.result, issue_description: recordForm.issue, resolution: recordForm.resolution, software_version_after: recordForm.softwareVersion, rule_library_version_after: recordForm.ruleLibraryVersion, inspection_task: recordForm.taskId || null }; if (editingRecordId.value) await updateResource('device-operation-records', editingRecordId.value, payload); else await createResource('device-operation-records', payload); recordDialogVisible.value = false; ElMessage.success(editingRecordId.value ? '运维记录已更新' : '运维记录已保存'); await load() } catch (error) { ElMessage.error(formatApiError(error, '保存运维记录失败')) } finally { saving.value = false } }
async function removeRecord(record) { try { await ElMessageBox.confirm('确认删除该运维记录？', '删除确认', { type: 'warning' }); await deleteResource('device-operation-records', record.id); ElMessage.success('运维记录已删除'); await load() } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(formatApiError(error, '删除运维记录失败')) } }
</script>

<style scoped>
.service-actions { display: flex; justify-content: flex-end; margin: 0 0 12px; }
.form-control { width: 100%; }
</style>
