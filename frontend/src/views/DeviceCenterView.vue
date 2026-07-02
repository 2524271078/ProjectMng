<template>
  <div>
    <div class="section-head">
      <div><span class="eyebrow-dark">Project Center</span><h2>项目中心</h2></div>
      <el-button type="primary" @click="openCreateDialog">新增项目</el-button>
    </div>
    <el-table :data="projects" stripe @row-click="openDetail">
      <el-table-column prop="project_no" label="项目编号" min-width="150" />
      <el-table-column prop="name" label="项目名称" min-width="220" />
      <el-table-column prop="project_stage" label="阶段" />
      <el-table-column prop="amount" label="金额" />
      <el-table-column prop="status" label="状态" />
    </el-table>

    <el-dialog v-model="dialogVisible" title="新增项目" width="620px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="项目编号"><el-input v-model="form.project_no" /></el-form-item>
        <el-form-item label="项目名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="客户"><OrganizationTreeSelect v-model="form.customer_org" placeholder="请选择客户" /></el-form-item>
        <el-form-item label="销售人员"><el-select v-model="form.sales_person" clearable filterable><el-option v-for="person in salesPeople" :key="person.id" :label="person.name" :value="person.id" /></el-select></el-form-item>
        <el-form-item label="项目阶段"><el-select v-model="form.project_stage"><el-option label="立项" value="new" /><el-option label="签约" value="signed" /><el-option label="交付" value="delivery" /><el-option label="运维" value="ops" /></el-select></el-form-item>
        <el-form-item label="项目金额"><el-input-number v-model="form.amount" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="createProject">保存</el-button></template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" size="58%" title="项目详情">
      <el-tabs v-if="overview" model-value="base">
        <el-tab-pane label="基础信息" name="base"><el-descriptions :column="2" border><el-descriptions-item label="项目编号">{{ overview.project.project_no }}</el-descriptions-item><el-descriptions-item label="项目名称">{{ overview.project.name }}</el-descriptions-item><el-descriptions-item label="客户">{{ overview.customer?.name || '-' }}</el-descriptions-item><el-descriptions-item label="销售">{{ overview.sales_person?.name || '-' }}</el-descriptions-item><el-descriptions-item label="阶段">{{ overview.project.project_stage }}</el-descriptions-item><el-descriptions-item label="金额">{{ overview.project.amount }}</el-descriptions-item></el-descriptions></el-tab-pane>
        <el-tab-pane label="项目设备" name="devices"><div class="action-row"><el-select v-model="deviceBinding.device" placeholder="选择设备" filterable><el-option v-for="device in devices" :key="device.id" :label="`${device.name} / ${device.serial_number}`" :value="device.id" /></el-select><el-input v-model="deviceBinding.deploy_location" placeholder="部署位置" /><el-button type="primary" @click="bindDevice">绑定设备</el-button></div><el-table :data="overview.devices"><el-table-column prop="name" label="设备" /><el-table-column prop="serial_number" label="序列号" /><el-table-column prop="quantity" label="数量" /><el-table-column prop="deploy_location" label="部署位置" /></el-table></el-tab-pane>
        <el-tab-pane label="合同和附件" name="attachments"><el-upload drag action="#" :auto-upload="false"><el-icon><UploadFilled /></el-icon><div>可上传合同、验收单、设备截图，后续接入附件上传 API</div></el-upload><el-table :data="overview.attachments"><el-table-column prop="name" label="附件名" /></el-table></el-tab-pane>
      </el-tabs>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import OrganizationTreeSelect from '../components/OrganizationTreeSelect.vue'
import { createResource, fetchProjectOverview, listResource, updateResource } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'

const projects = ref([])
const devices = ref([])
const salesPeople = ref([])
const overview = ref(null)
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const activeProjectId = ref(null)
const form = reactive({ project_no: '', name: '', customer_org: null, sales_person: null, project_stage: 'new', amount: 0 })
const deviceBinding = reactive({ device: null, deploy_location: '', hardware_code: '', software_version: '', license_info_text: '', is_under_warranty: false, screenshot_url: '' })
async function loadProjects() { const { data } = await listResource('projects'); projects.value = unwrapList(data) }
async function loadOptions() { devices.value = unwrapList((await listResource('devices')).data); salesPeople.value = unwrapList((await listResource('people')).data).filter((p) => p.person_type === 'sales') }
function openCreateDialog() { Object.assign(form, { project_no: '', name: '', customer_org: null, sales_person: null, project_stage: 'new', amount: 0 }); dialogVisible.value = true }
async function createProject() { try { await createResource('projects', form); ElMessage.success('项目已新增'); dialogVisible.value = false; await loadProjects() } catch (error) { ElMessage.error(formatApiError(error, '新增项目失败')) } }
async function openDetail(row) { activeProjectId.value = row.id; const { data } = await fetchProjectOverview(row.id); overview.value = data; drawerVisible.value = true }

function parseLicenseInfo() {
  const text = deviceBinding.license_info_text?.trim()
  if (!text) return {}
  try {
    return JSON.parse(text)
  } catch {
    return { description: text }
  }
}

function fillDeviceFields(deviceId) {
  const device = devices.value.find((item) => item.id === deviceId)
  if (!device) return
  deviceBinding.hardware_code = device.hardware_code || ''
  deviceBinding.software_version = device.software_version || ''
  deviceBinding.license_info_text = device.license_info ? JSON.stringify(device.license_info) : ''
  deviceBinding.is_under_warranty = Boolean(device.is_under_warranty)
  deviceBinding.screenshot_url = device.screenshot_url || ''
}

async function bindDevice() { try { await createResource('project-devices', { project: activeProjectId.value, device: deviceBinding.device, quantity: 1, deploy_location: deviceBinding.deploy_location }); Object.assign(deviceBinding, { device: null, deploy_location: '' }); await openDetail({ id: activeProjectId.value }) } catch (error) { ElMessage.error(formatApiError(error, '绑定设备失败')) } }
onMounted(async () => { await Promise.all([loadProjects(), loadOptions()]) })
</script>
