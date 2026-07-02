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

    <el-drawer v-model="drawerVisible" size="70%" title="项目详情">
      <el-tabs v-if="overview" model-value="base">
        <el-tab-pane label="基础信息" name="base">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目编号">{{ overview.project.project_no }}</el-descriptions-item>
            <el-descriptions-item label="项目名称">{{ overview.project.name }}</el-descriptions-item>
            <el-descriptions-item label="客户">{{ overview.customer?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="销售">{{ overview.sales_person?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="阶段">{{ overview.project.project_stage }}</el-descriptions-item>
            <el-descriptions-item label="金额">{{ overview.project.amount }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <el-tab-pane label="项目设备" name="devices">
          <el-card shadow="never" class="mb-16">
            <template #header>选择设备并补充项目设备信息</template>
            <el-form :model="deviceBinding" label-width="130px">
              <el-row :gutter="14">
                <el-col :span="24"><el-form-item label="设备来源"><el-radio-group v-model="deviceBinding.bind_mode"><el-radio-button label="existing">选择已有设备</el-radio-button><el-radio-button label="new">新建设备</el-radio-button></el-radio-group></el-form-item></el-col>
                <el-col v-if="deviceBinding.bind_mode === 'existing'" :span="12"><el-form-item label="选择设备"><el-select v-model="deviceBinding.device" placeholder="选择设备" filterable @change="fillDeviceFields"><el-option v-for="device in devices" :key="device.id" :label="`${device.name} / ${device.serial_number}`" :value="device.id" /></el-select></el-form-item></el-col>
                <template v-else>
                  <el-col :span="12"><el-form-item label="产品型号"><el-select v-model="deviceBinding.device_model" placeholder="选择产品型号" filterable><el-option v-for="model in deviceModels" :key="model.id" :label="`${model.model_name} / ${model.model_code}`" :value="model.id" /></el-select></el-form-item></el-col>
                  <el-col :span="12"><el-form-item label="设备名称"><el-input v-model="deviceBinding.device_name" /></el-form-item></el-col>
                  <el-col :span="12"><el-form-item label="序列号"><el-input v-model="deviceBinding.serial_number" /></el-form-item></el-col>
                </template>
                <el-col :span="12"><el-form-item label="设备项目类型"><el-input v-model="deviceBinding.device_project_type" placeholder="如：正式设备/试点设备/备机" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="部署位置"><el-input v-model="deviceBinding.deploy_location" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="管理地址"><el-input v-model="deviceBinding.management_address" placeholder="IP / URL / 管理平台地址" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="设备硬件码"><el-input v-model="deviceBinding.hardware_code" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="设备系统版本"><el-input v-model="deviceBinding.software_version" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="版本更新方式"><el-input v-model="deviceBinding.version_update_method" placeholder="远程升级/现场升级/手动导入" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="上架时间"><el-date-picker v-model="deviceBinding.rack_install_date" type="date" value-format="YYYY-MM-DD" placeholder="选择上架时间" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="是否标品"><el-switch v-model="deviceBinding.is_standard_product" active-text="标品" inactive-text="非标" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="是否支持远程"><el-switch v-model="deviceBinding.supports_remote" active-text="支持" inactive-text="不支持" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="是否保内"><el-switch v-model="deviceBinding.is_under_warranty" active-text="保内" inactive-text="保外" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="现场运维人员"><el-select v-model="deviceBinding.ops_person" clearable filterable><el-option v-for="person in opsPeople" :key="person.id" :label="person.name" :value="person.id" /></el-select></el-form-item></el-col>
                <el-col :span="24"><el-form-item label="授权信息"><el-input v-model="deviceBinding.license_info_text" type="textarea" placeholder="可填 JSON，也可直接写授权说明" /></el-form-item></el-col>
                <el-col :span="24"><el-form-item label="设备截图链接"><el-input v-model="deviceBinding.screenshot_url" placeholder="https://..." /></el-form-item></el-col>
                <el-col :span="24"><el-form-item label="上传截图"><el-upload :auto-upload="false" :on-change="uploadDeviceScreenshot" :show-file-list="false"><el-button>选择并上传截图</el-button></el-upload><div v-if="uploadedScreenshots.length" class="upload-preview"><a v-for="item in uploadedScreenshots" :key="item.id" :href="item.file_url" target="_blank">{{ item.name }}</a></div></el-form-item></el-col>
                <el-col :span="24"><el-form-item label="备注"><el-input v-model="deviceBinding.remark" type="textarea" /></el-form-item></el-col>
              </el-row>
              <el-button type="primary" @click="bindDevice">保存并绑定设备</el-button>
            </el-form>
          </el-card>

          <el-table :data="overview.devices" stripe>
            <el-table-column prop="name" label="设备" min-width="140" />
            <el-table-column prop="serial_number" label="序列号" min-width="140" />
            <el-table-column prop="device_project_type" label="设备项目类型" />
            <el-table-column prop="management_address" label="管理地址" min-width="160" />
            <el-table-column prop="hardware_code" label="硬件码" />
            <el-table-column prop="software_version" label="系统版本" />
            <el-table-column prop="version_update_method" label="版本更新方式" />
            <el-table-column prop="rack_install_date" label="上架时间" />
            <el-table-column label="标品"><template #default="scope">{{ scope.row.is_standard_product ? '是' : '否' }}</template></el-table-column>
            <el-table-column label="远程"><template #default="scope">{{ scope.row.supports_remote ? '支持' : '不支持' }}</template></el-table-column>
            <el-table-column label="保内"><template #default="scope">{{ scope.row.is_under_warranty ? '保内' : '保外' }}</template></el-table-column>
            <el-table-column label="现场运维"><template #default="scope">{{ scope.row.ops_person?.name || '-' }}</template></el-table-column>
            <el-table-column prop="deploy_location" label="部署位置" />
            <el-table-column prop="screenshot_url" label="截图链接" min-width="180"><template #default="scope"><a v-if="scope.row.screenshot_url" :href="scope.row.screenshot_url" target="_blank">预览</a><span v-else>-</span></template></el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="合同和附件" name="attachments">
          <el-upload drag action="#" :auto-upload="false" :on-change="uploadProjectAttachment" :show-file-list="false">
            <el-icon><UploadFilled /></el-icon>
            <div>上传合同、验收单、项目资料等附件</div>
          </el-upload>
          <el-table :data="overview.attachments" class="mt-16">
            <el-table-column prop="name" label="附件名" />
            <el-table-column prop="uploaded_at" label="上传时间" />
            <el-table-column label="操作" width="160">
              <template #default="scope">
                <el-button v-if="scope.row.file_url" link type="primary" @click.stop="previewAttachment(scope.row)">预览</el-button>
                <el-button v-if="scope.row.file_url" link type="primary" @click.stop="downloadAttachment(scope.row)">下载</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import OrganizationTreeSelect from '../components/OrganizationTreeSelect.vue'
import { createResource, fetchProjectOverview, listResource, updateResource, uploadAttachment } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'

const projects = ref([])
const devices = ref([])
const deviceModels = ref([])
const uploadedScreenshots = ref([])
const salesPeople = ref([])
const opsPeople = ref([])
const overview = ref(null)
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const activeProjectId = ref(null)
const form = reactive({ project_no: '', name: '', customer_org: null, sales_person: null, project_stage: 'new', amount: 0 })
const deviceBinding = reactive(defaultDeviceBinding())

function defaultDeviceBinding() {
  return {
    bind_mode: 'existing',
    device: null,
    device_model: null,
    device_name: '',
    serial_number: '',
    deploy_location: '',
    device_project_type: '',
    management_address: '',
    hardware_code: '',
    software_version: '',
    version_update_method: '',
    license_info_text: '',
    is_standard_product: true,
    is_under_warranty: false,
    supports_remote: false,
    ops_person: null,
    screenshot_url: '',
    rack_install_date: '',
    remark: '',
  }
}

async function loadProjects() {
  const { data } = await listResource('projects')
  projects.value = unwrapList(data)
}

async function loadOptions() {
  devices.value = unwrapList((await listResource('devices')).data)
  deviceModels.value = unwrapList((await listResource('device-models')).data)
  const people = unwrapList((await listResource('people')).data)
  salesPeople.value = people.filter((person) => person.person_type === 'sales')
  opsPeople.value = people.filter((person) => person.person_type === 'ops' || person.person_type === 'internal')
}

function openCreateDialog() {
  Object.assign(form, { project_no: '', name: '', customer_org: null, sales_person: null, project_stage: 'new', amount: 0 })
  dialogVisible.value = true
}

async function createProject() {
  try {
    await createResource('projects', form)
    ElMessage.success('项目已新增')
    dialogVisible.value = false
    await loadProjects()
  } catch (error) {
    ElMessage.error(formatApiError(error, '新增项目失败'))
  }
}

async function openDetail(row) {
  activeProjectId.value = row.id
  const { data } = await fetchProjectOverview(row.id)
  overview.value = data
  drawerVisible.value = true
}


async function ensureDevice() {
  if (deviceBinding.bind_mode === 'existing') {
    if (!deviceBinding.device) throw new Error('请选择设备')
    return deviceBinding.device
  }
  if (!deviceBinding.device_model) throw new Error('请选择产品型号')
  if (!deviceBinding.device_name?.trim()) throw new Error('请填写设备名称')
  if (!deviceBinding.serial_number?.trim()) throw new Error('请填写设备序列号')
  const { data } = await createResource('devices', {
    name: deviceBinding.device_name,
    serial_number: deviceBinding.serial_number,
    device_model: deviceBinding.device_model,
  })
  deviceBinding.device = data.id
  return data.id
}


async function uploadProjectAttachment(file) {
  try {
    if (!activeProjectId.value) return ElMessage.warning('请先打开项目详情')
    const payload = new FormData()
    payload.append('name', file.name)
    payload.append('object_type', 'project')
    payload.append('object_id', activeProjectId.value)
    payload.append('file', file.raw)
    await uploadAttachment(payload)
    ElMessage.success('附件已上传')
    await openDetail({ id: activeProjectId.value })
  } catch (error) {
    ElMessage.error(formatApiError(error, '上传附件失败'))
  }
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

async function uploadDeviceScreenshot(file) {
  try {
    const deviceId = await ensureDevice()
    const payload = new FormData()
    payload.append('name', file.name)
    payload.append('object_type', 'device')
    payload.append('object_id', deviceId)
    payload.append('file', file.raw)
    const { data } = await uploadAttachment(payload)
    uploadedScreenshots.value.push(data)
    deviceBinding.screenshot_url = data.file_url
    ElMessage.success('截图已上传')
  } catch (error) {
    ElMessage.error(error.message || formatApiError(error, '上传截图失败'))
  }
}

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
  Object.assign(deviceBinding, {
    management_address: device.management_address || '',
    hardware_code: device.hardware_code || '',
    software_version: device.software_version || '',
    version_update_method: device.version_update_method || '',
    license_info_text: device.license_info ? JSON.stringify(device.license_info) : '',
    is_standard_product: device.is_standard_product ?? true,
    is_under_warranty: Boolean(device.is_under_warranty),
    supports_remote: Boolean(device.supports_remote),
    ops_person: device.ops_person || null,
    screenshot_url: device.screenshot_url || '',
    rack_install_date: device.rack_install_date || '',
    remark: device.remark || '',
  })
}

async function bindDevice() {
  try {
    const deviceId = await ensureDevice()
    await updateResource('devices', deviceId, {
      management_address: deviceBinding.management_address,
      hardware_code: deviceBinding.hardware_code,
      software_version: deviceBinding.software_version,
      version_update_method: deviceBinding.version_update_method,
      license_info: parseLicenseInfo(),
      is_standard_product: deviceBinding.is_standard_product,
      is_under_warranty: deviceBinding.is_under_warranty,
      supports_remote: deviceBinding.supports_remote,
      ops_person: deviceBinding.ops_person,
      screenshot_url: deviceBinding.screenshot_url,
      rack_install_date: deviceBinding.rack_install_date || null,
      remark: deviceBinding.remark,
    })
    await createResource('project-devices', {
      project: activeProjectId.value,
      device: deviceId,
      quantity: 1,
      deploy_location: deviceBinding.deploy_location,
      device_project_type: deviceBinding.device_project_type,
    })
    Object.assign(deviceBinding, defaultDeviceBinding())
    uploadedScreenshots.value = []
    await loadOptions()
    await openDetail({ id: activeProjectId.value })
  } catch (error) {
    ElMessage.error(formatApiError(error, '绑定设备失败'))
  }
}

onMounted(async () => { await Promise.all([loadProjects(), loadOptions()]) })
</script>
