<template>
  <div>
    <div class="section-head">
      <div><span class="eyebrow-dark">Project Center</span><h2>项目中心</h2></div>
      <el-button type="primary" @click="openCreateDialog">新增项目</el-button>
    </div>

    <el-table :data="projects" stripe @row-click="openDetail">
      <el-table-column prop="project_no" label="项目编号" min-width="150" />
      <el-table-column prop="name" label="项目名称" min-width="220" />
      <el-table-column label="阶段">
        <template #default="scope">{{ projectStageLabel(scope.row.project_stage) }}</template>
      </el-table-column>
      <el-table-column prop="winning_company" label="实际中标公司" min-width="160" />
      <el-table-column prop="contact_company" label="对接公司" min-width="160" />
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click.stop="openEditDialog(scope.row)">编辑</el-button>
          <el-button link type="danger" @click.stop="removeProject(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingProjectId ? '编辑项目' : '新增项目'" width="620px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="项目编号"><el-input v-model="form.project_no" /></el-form-item>
        <el-form-item label="项目名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="客户公司"><OrganizationTreeSelect v-model="form.customer_org" placeholder="请选择客户公司" /></el-form-item>
        <el-form-item label="客户联系人" required>
          <el-select v-model="form.customer_contact" placeholder="请选择客户联系人" filterable clearable :disabled="!customerContacts.length">
            <el-option v-for="person in customerContacts" :key="person.id" :label="person.position ? `${person.name} / ${person.position}` : person.name" :value="person.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="实际中标公司"><el-input v-model="form.winning_company" /></el-form-item>
        <el-form-item label="对接公司"><el-input v-model="form.contact_company" /></el-form-item>
        <el-form-item label="销售人员"><el-select v-model="form.sales_person" clearable filterable><el-option v-for="person in salesPeople" :key="person.id" :label="person.name" :value="person.id" /></el-select></el-form-item>
        <el-form-item label="项目阶段"><el-select v-model="form.project_stage"><el-option label="立项" value="new" /><el-option label="签约" value="signed" /><el-option label="交付" value="delivery" /><el-option label="运维" value="ops" /></el-select></el-form-item>
        <el-form-item label="项目金额"><el-input-number v-model="form.amount" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="createProject">{{ editingProjectId ? '保存修改' : '保存' }}</el-button></template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" size="70%" title="项目详情">
      <el-tabs v-if="overview" model-value="base">
        <el-tab-pane label="基础信息" name="base">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目编号">{{ overview.project.project_no }}</el-descriptions-item>
            <el-descriptions-item label="项目名称">{{ overview.project.name }}</el-descriptions-item>
            <el-descriptions-item label="客户公司">{{ overview.customer?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="客户联系人">{{ overview.customer_contact?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="联系人职位">{{ overview.customer_contact?.position || '-' }}</el-descriptions-item>
            <el-descriptions-item label="实际中标公司">{{ overview.project.winning_company || '-' }}</el-descriptions-item>
            <el-descriptions-item label="对接公司">{{ overview.project.contact_company || '-' }}</el-descriptions-item>
            <el-descriptions-item label="销售">{{ overview.sales_person?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="阶段">{{ projectStageLabel(overview.project.project_stage) }}</el-descriptions-item>
            <el-descriptions-item label="金额">{{ overview.project.amount }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <el-tab-pane label="项目设备" name="devices">
          <el-card shadow="never" class="mb-16">
            <template #header>
              <div class="section-head compact"><span>{{ editingProjectDeviceId ? '编辑项目设备' : '新增项目设备' }}</span><div><el-button v-if="editingProjectDeviceId" link @click="resetDeviceBinding">取消编辑</el-button><el-button link type="primary" @click="toggleDeviceMode">{{ deviceBinding.bind_mode === 'new' ? '选择已有设备' : '改为新建设备' }}</el-button></div></div>
            </template>
            <el-form :model="deviceBinding" label-width="130px">
              <el-row :gutter="14">
                <el-col v-if="deviceBinding.bind_mode === 'existing'" :span="24">
                  <el-alert v-if="!customerScopedDevices.length" title="当前客户下暂无已购设备，请切换到“新建设备”后补录。" type="warning" show-icon :closable="false" class="mb-16" />
                  <el-form-item label="选择已有设备"><el-select v-model="deviceBinding.device" placeholder="选择当前客户下的设备实例" filterable @change="fillDeviceFields"><el-option v-for="device in customerScopedDevices" :key="device.id" :label="formatDeviceOptionLabel(device, deviceModels)" :value="device.id" /></el-select></el-form-item>
                </el-col>
                <template v-else>
                  <el-col :span="24"><el-alert title="默认流程：选择产品型号，填写这台设备的序列号等信息，保存后会自动创建设备并绑定到当前项目和当前客户。" type="info" show-icon :closable="false" class="mb-16" /></el-col>
                  <el-col :span="12"><el-form-item label="产品型号" required><el-select v-model="deviceBinding.device_model" placeholder="选择产品中心维护的具体型号" filterable><el-option v-for="model in deviceModels" :key="model.id" :label="`${model.model_name} / ${model.model_code}`" :value="model.id" /></el-select></el-form-item></el-col>
                  <el-col :span="12"><el-form-item label="设备名称" required><el-input v-model="deviceBinding.device_name" /></el-form-item></el-col>
                  <el-col :span="12"><el-form-item label="序列号" required><el-input v-model="deviceBinding.serial_number" /></el-form-item></el-col>
                </template>
                <el-col :span="12"><el-form-item label="设备项目类型"><el-input v-model="deviceBinding.device_project_type" placeholder="如：正式设备/试点设备/备机" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="部署位置"><el-input v-model="deviceBinding.deploy_location" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="管理地址"><el-input v-model="deviceBinding.management_address" placeholder="IP / URL / 管理平台地址" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="设备硬件码"><el-input v-model="deviceBinding.hardware_code" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="设备系统版本"><el-input v-model="deviceBinding.software_version" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="版本更新方式"><el-input v-model="deviceBinding.version_update_method" placeholder="远程升级/现场升级/手动导入" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="服务类型"><el-select v-model="deviceBinding.service_type"><el-option label="新装" value="new_install" /><el-option label="续保" value="renewal" /></el-select></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="服务开始"><el-date-picker v-model="deviceBinding.service_start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择服务开始日期" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="服务结束"><el-date-picker v-model="deviceBinding.service_end_date" type="date" value-format="YYYY-MM-DD" placeholder="选择服务结束日期" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="上架时间"><el-date-picker v-model="deviceBinding.rack_install_date" type="date" value-format="YYYY-MM-DD" placeholder="选择上架时间" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="是否标品"><el-switch v-model="deviceBinding.is_standard_product" active-text="标品" inactive-text="非标" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="是否支持远程"><el-switch v-model="deviceBinding.supports_remote" active-text="支持" inactive-text="不支持" /></el-form-item></el-col>
                <el-col :span="12"><el-form-item label="现场运维人员"><el-select v-model="deviceBinding.ops_person" clearable filterable><el-option v-for="person in opsPeople" :key="person.id" :label="person.name" :value="person.id" /></el-select></el-form-item></el-col>
                <el-col :span="24"><el-form-item label="授权信息"><el-input v-model="deviceBinding.license_info_text" type="textarea" placeholder="可填 JSON，也可直接写授权说明" /></el-form-item></el-col>
                <el-col :span="24"><el-form-item label="设备截图链接"><el-input v-model="deviceBinding.screenshot_url" placeholder="https://..." /></el-form-item></el-col>
                <el-col :span="24"><el-form-item label="上传截图"><el-upload :auto-upload="false" :on-change="uploadDeviceScreenshot" :show-file-list="false"><el-button>选择并上传截图</el-button></el-upload><div v-if="uploadedScreenshots.length" class="upload-preview"><a v-for="item in uploadedScreenshots" :key="item.id" :href="item.file_url" target="_blank">{{ item.name }}</a></div></el-form-item></el-col>
                <el-col :span="24"><el-form-item label="备注"><el-input v-model="deviceBinding.remark" type="textarea" /></el-form-item></el-col>
              </el-row>
              <el-button type="primary" @click="bindDevice">{{ editingProjectDeviceId ? '保存修改' : (deviceBinding.bind_mode === 'new' ? '保存项目设备' : '绑定已有设备') }}</el-button>
            </el-form>
          </el-card>

          <el-table :data="overview.devices" stripe>
            <el-table-column prop="name" label="设备" min-width="160" />
            <el-table-column prop="serial_number" label="序列号" min-width="160" />
            <el-table-column prop="device_project_type" label="项目类型" min-width="120" />
            <el-table-column label="服务类型" min-width="100">
              <template #default="scope">{{ serviceTypeLabel(scope.row.service_type) }}</template>
            </el-table-column>
            <el-table-column prop="service_start_date" label="服务开始" min-width="120" />
            <el-table-column prop="service_end_date" label="服务结束" min-width="120" />
            <el-table-column label="保内状态" min-width="100">
              <template #default="scope">{{ scope.row.service_status || '-' }}</template>
            </el-table-column>
            <el-table-column prop="management_address" label="管理地址" min-width="180" />
            <el-table-column label="现场运维" min-width="120">
              <template #default="scope">{{ scope.row.ops_person?.name || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="170" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click.stop="editProjectDevice(scope.row)">编辑</el-button>
                <el-button link type="danger" @click.stop="removeProjectDevice(scope.row)">删除</el-button>
                <el-button link type="primary" @click.stop="openDeviceDetail(scope.row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="关联合同" name="contracts">
          <el-form inline class="mb-16">
            <el-form-item label="选择合同">
              <el-select v-model="selectedContractId" filterable clearable placeholder="选择该客户相关合同">
                <el-option v-for="contract in customerScopedContracts" :key="contract.id" :label="`${contract.contract_no} / ${contract.contract_name}`" :value="contract.id" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="bindContract">关联合同</el-button>
          </el-form>
          <el-table :data="overview.contracts || []" stripe>
            <el-table-column prop="contract_no" label="合同编号" min-width="150" />
            <el-table-column prop="contract_name" label="合同名称" min-width="220" />
            <el-table-column prop="amount" label="金额" min-width="120" />
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button link type="danger" @click.stop="removeProjectContract(scope.row)">解除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="项目附件" name="attachments">
          <el-upload drag action="#" :auto-upload="false" :on-change="uploadProjectAttachment" :show-file-list="false">
            <el-icon><UploadFilled /></el-icon>
            <div>上传合同、验收单、项目资料等附件</div>
          </el-upload>
          <el-table :data="overview.attachments" class="mt-16">
            <el-table-column prop="name" label="附件名" min-width="240" show-overflow-tooltip />
            <el-table-column prop="uploaded_at" label="上传时间" min-width="180" />
            <el-table-column label="操作" width="190">
              <template #default="scope">
                <el-space wrap size="small">
                  <el-button v-if="scope.row.file_url" link type="primary" @click.stop="previewAttachment(scope.row)">预览</el-button>
                  <el-button v-if="scope.row.file_url" link type="primary" @click.stop="downloadAttachment(scope.row)">下载</el-button>
                  <el-button link type="danger" @click.stop="removeAttachment(scope.row)">删除</el-button>
                </el-space>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>

    <el-dialog v-model="deviceDetailVisible" title="设备详情" width="860px">
      <el-descriptions v-if="selectedDevice" :column="2" border>
        <el-descriptions-item label="设备名称">{{ selectedDevice.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="序列号">{{ selectedDevice.serial_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备项目类型">{{ selectedDevice.device_project_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="管理地址">{{ selectedDevice.management_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备硬件码">{{ selectedDevice.hardware_code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备系统版本">{{ selectedDevice.software_version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="版本更新方式">{{ selectedDevice.version_update_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="服务类型">{{ serviceTypeLabel(selectedDevice.service_type) }}</el-descriptions-item>
        <el-descriptions-item label="服务开始">{{ selectedDevice.service_start_date || selectedDevice.current_service_start_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="服务结束">{{ selectedDevice.service_end_date || selectedDevice.current_service_end_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="保内状态">{{ selectedDevice.service_status || selectedDevice.current_service_status || '-' }}</el-descriptions-item>
        <el-descriptions-item label="上架时间">{{ selectedDevice.rack_install_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="是否标品">{{ selectedDevice.is_standard_product ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否支持远程">{{ selectedDevice.supports_remote ? '支持' : '不支持' }}</el-descriptions-item>
        <el-descriptions-item label="现场运维人员">{{ selectedDevice.ops_person?.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="部署位置">{{ selectedDevice.deploy_location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="截图链接">
          <a v-if="selectedDevice.screenshot_url" :href="selectedDevice.screenshot_url" target="_blank" rel="noopener noreferrer">预览</a>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="授权信息" :span="2">{{ typeof selectedDevice.license_info === 'string' ? selectedDevice.license_info : JSON.stringify(selectedDevice.license_info || {}) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ selectedDevice.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import OrganizationTreeSelect from '../components/OrganizationTreeSelect.vue'
import { createProjectContract, createResource, deleteProjectContract, deleteResource, fetchCustomerOverview, fetchProjectOverview, listResource, updateResource, uploadAttachment } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'
import { formatDeviceOptionLabel } from '../utils/deviceOptions'
import { buildProjectDeviceBindingPayload, buildProjectDevicePayload, createDefaultProjectDeviceForm } from '../utils/projectDeviceForm'
import { projectStageLabel, serviceTypeLabel } from '../utils/displayMaps'

const projects = ref([])
const devices = ref([])
const customerOverview = ref(null)
const contracts = ref([])
const deviceModels = ref([])
const uploadedScreenshots = ref([])
const salesPeople = ref([])
const opsPeople = ref([])
const customerContacts = ref([])
const overview = ref(null)
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const editingProjectId = ref(null)
const deviceDetailVisible = ref(false)
const activeProjectId = ref(null)
const editingProjectDeviceId = ref(null)
const selectedDevice = ref(null)
const selectedContractId = ref(null)
const form = reactive({ project_no: '', name: '', customer_org: null, customer_contact: null, winning_company: '', contact_company: '', sales_person: null, project_stage: 'new', amount: 0 })
const deviceBinding = reactive(defaultDeviceBinding())

const customerScopedDevices = computed(() => {
  if (customerOverview.value?.devices?.length) return customerOverview.value.devices
  const customerId = overview.value?.customer?.id
  if (!customerId) return devices.value
  return devices.value.filter((device) => device.customer_org === customerId)
})

const customerScopedContracts = computed(() => {
  const customerId = overview.value?.customer?.id
  if (!customerId) return contracts.value
  return contracts.value.filter((contract) => contract.final_customer === customerId)
})

function defaultDeviceBinding() {
  return createDefaultProjectDeviceForm()
}

function resetDeviceBinding() {
  editingProjectDeviceId.value = null
  Object.assign(deviceBinding, defaultDeviceBinding())
  uploadedScreenshots.value = []
}

function toggleDeviceMode() {
  const nextMode = deviceBinding.bind_mode === 'new' ? 'existing' : 'new'
  editingProjectDeviceId.value = null
  Object.assign(deviceBinding, defaultDeviceBinding(), { bind_mode: nextMode, service_type: nextMode === 'existing' ? 'renewal' : 'new_install' })
  uploadedScreenshots.value = []
}

async function loadCustomerContacts(customerOrgId) {
  customerContacts.value = []
  form.customer_contact = null
  if (!customerOrgId) return
  const { data } = await fetchCustomerOverview(customerOrgId)
  customerContacts.value = data.contacts || []
}

async function loadProjects() {
  const { data } = await listResource('projects')
  projects.value = unwrapList(data)
}

async function loadOptions() {
  devices.value = unwrapList((await listResource('devices')).data)
  contracts.value = unwrapList((await listResource('contracts')).data)
  deviceModels.value = unwrapList((await listResource('device-models')).data)
  const people = unwrapList((await listResource('people')).data)
  salesPeople.value = people.filter((person) => person.person_type === 'sales')
  opsPeople.value = people.filter((person) => person.person_type === 'ops' || person.person_type === 'internal')
}

function resetProjectForm() {
  Object.assign(form, { project_no: '', name: '', customer_org: null, customer_contact: null, winning_company: '', contact_company: '', sales_person: null, project_stage: 'new', amount: 0 })
}

function openCreateDialog() {
  editingProjectId.value = null
  resetProjectForm()
  customerContacts.value = []
  dialogVisible.value = true
}

async function openEditDialog(row) {
  editingProjectId.value = row.id
  Object.assign(form, {
    project_no: row.project_no || '',
    name: row.name || '',
    customer_org: row.customer_org || null,
    customer_contact: row.customer_contact || null,
    winning_company: row.winning_company || '',
    contact_company: row.contact_company || '',
    sales_person: row.sales_person || null,
    project_stage: row.project_stage || 'new',
    amount: Number(row.amount || 0),
  })
  await loadCustomerContacts(form.customer_org)
  form.customer_contact = row.customer_contact || null
  dialogVisible.value = true
}

async function createProject() {
  try {
    if (form.customer_org && !form.customer_contact) {
      ElMessage.warning('请选择客户公司下的联系人')
      return
    }
    if (editingProjectId.value) {
      await updateResource('projects', editingProjectId.value, form)
      ElMessage.success('项目已更新')
    } else {
      await createResource('projects', form)
      ElMessage.success('项目已新增')
    }
    dialogVisible.value = false
    editingProjectId.value = null
    resetProjectForm()
    await loadProjects()
    if (activeProjectId.value) {
      const currentProjectId = activeProjectId.value
      const exists = projects.value.some((item) => item.id === currentProjectId)
      if (exists) await openDetail({ id: currentProjectId })
    }
  } catch (error) {
    ElMessage.error(formatApiError(error, editingProjectId.value ? '更新项目失败' : '新增项目失败'))
  }
}

async function openDetail(row) {
  activeProjectId.value = row.id
  selectedContractId.value = null
  customerOverview.value = null
  const { data } = await fetchProjectOverview(row.id)
  overview.value = data
  if (data.customer?.id) {
    const customerResult = await fetchCustomerOverview(data.customer.id)
    customerOverview.value = customerResult.data
  }
  drawerVisible.value = true
}

async function removeProject(row) {
  try {
    await ElMessageBox.confirm(`确认删除项目“${row.name}”？`, '删除确认', { type: 'warning' })
    await deleteResource('projects', row.id)
    ElMessage.success('项目已删除')
    if (activeProjectId.value === row.id) {
      drawerVisible.value = false
      activeProjectId.value = null
      overview.value = null
      customerOverview.value = null
    }
    await loadProjects()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(formatApiError(error, '删除项目失败'))
  }
}

function currentDeviceOwner() {
  return {
    customerOrgId: overview.value?.customer?.id,
    salesPersonId: overview.value?.sales_person?.id,
  }
}

async function ensureDevice() {
  if (deviceBinding.bind_mode === 'existing') {
    if (!deviceBinding.device) throw new Error('请选择设备')
    return deviceBinding.device
  }
  if (deviceBinding.device) return deviceBinding.device
  if (!deviceBinding.device_model) throw new Error('请选择产品型号')
  if (!deviceBinding.device_name?.trim()) throw new Error('请填写设备名称')
  if (!deviceBinding.serial_number?.trim()) throw new Error('请填写设备序列号')
  const { data } = await createResource('devices', buildProjectDevicePayload(deviceBinding, currentDeviceOwner()))
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

async function removeAttachment(row) {
  try {
    await ElMessageBox.confirm(`确认删除附件“${row.name}”？`, '删除确认', { type: 'warning' })
    await deleteResource('attachments', row.id)
    ElMessage.success('附件已删除')
    await openDetail({ id: activeProjectId.value })
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(formatApiError(error, '删除附件失败'))
  }
}

function openDeviceDetail(device) {
  selectedDevice.value = device
  deviceDetailVisible.value = true
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

function findSelectedDevice(deviceId) {
  return customerScopedDevices.value.find((item) => item.id === deviceId) || devices.value.find((item) => item.id === deviceId) || null
}

function findCurrentProjectBinding(deviceId) {
  const device = findSelectedDevice(deviceId)
  if (!device || !overview.value?.devices?.length) return null
  return overview.value.devices.find((item) => item.serial_number && item.serial_number === device.serial_number) || null
}

function fillDeviceFields(deviceId) {
  const device = findSelectedDevice(deviceId)
  if (!device) return
  const binding = findCurrentProjectBinding(deviceId)
  Object.assign(deviceBinding, {
    deploy_location: binding?.deploy_location || '',
    device_project_type: binding?.device_project_type || '',
    management_address: device.management_address || '',
    hardware_code: device.hardware_code || '',
    software_version: device.software_version || '',
    version_update_method: device.version_update_method || '',
    license_info_text: device.license_info ? JSON.stringify(device.license_info) : '',
    is_standard_product: device.is_standard_product ?? true,
    supports_remote: Boolean(device.supports_remote),
    service_type: binding?.service_type || 'renewal',
    service_start_date: binding?.service_start_date || device.current_service_start_date || '',
    service_end_date: binding?.service_end_date || device.current_service_end_date || '',
    ops_person: device.ops_person || null,
    screenshot_url: device.screenshot_url || '',
    rack_install_date: device.rack_install_date || '',
    remark: device.remark || '',
  })
}

function editProjectDevice(row) {
  editingProjectDeviceId.value = row.id
  Object.assign(deviceBinding, defaultDeviceBinding(), {
    bind_mode: 'existing',
    device: row.device_id || null,
    deploy_location: row.deploy_location || '',
    device_project_type: row.device_project_type || '',
    management_address: row.management_address || '',
    hardware_code: row.hardware_code || '',
    software_version: row.software_version || '',
    version_update_method: row.version_update_method || '',
    license_info_text: row.license_info ? JSON.stringify(row.license_info) : '',
    is_standard_product: row.is_standard_product ?? true,
    supports_remote: Boolean(row.supports_remote),
    service_type: row.service_type || 'renewal',
    service_start_date: row.service_start_date || '',
    service_end_date: row.service_end_date || '',
    ops_person: row.ops_person?.id || row.ops_person || null,
    screenshot_url: row.screenshot_url || '',
    rack_install_date: row.rack_install_date || '',
    remark: row.remark || '',
  })
  uploadedScreenshots.value = []
}

async function removeProjectDevice(row) {
  try {
    await ElMessageBox.confirm(`确认删除项目设备“${row.name}”？`, '删除确认', { type: 'warning' })
    await deleteResource('project-devices', row.id)
    ElMessage.success('项目设备已删除')
    if (editingProjectDeviceId.value === row.id) resetDeviceBinding()
    await openDetail({ id: activeProjectId.value })
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(formatApiError(error, '删除项目设备失败'))
  }
}

async function bindDevice() {
  try {
    if (!deviceBinding.service_start_date) throw new Error('请选择服务开始日期')
    if (!deviceBinding.service_end_date) throw new Error('请选择服务结束日期')
    if (deviceBinding.service_end_date < deviceBinding.service_start_date) throw new Error('服务结束日期不能早于开始日期')
    const deviceId = await ensureDevice()
    await updateResource('devices', deviceId, {
      management_address: deviceBinding.management_address,
      hardware_code: deviceBinding.hardware_code,
      software_version: deviceBinding.software_version,
      version_update_method: deviceBinding.version_update_method,
      license_info: parseLicenseInfo(),
      is_standard_product: deviceBinding.is_standard_product,
      supports_remote: deviceBinding.supports_remote,
      ops_person: deviceBinding.ops_person,
      screenshot_url: deviceBinding.screenshot_url,
      rack_install_date: deviceBinding.rack_install_date || null,
      remark: deviceBinding.remark,
    })
    const existingBinding = editingProjectDeviceId.value ? { id: editingProjectDeviceId.value } : findCurrentProjectBinding(deviceId)
    if (existingBinding) {
      await updateResource('project-devices', existingBinding.id, buildProjectDeviceBindingPayload(deviceBinding))
    } else {
      await createResource('project-devices', {
        project: activeProjectId.value,
        device: deviceId,
        ...buildProjectDeviceBindingPayload(deviceBinding),
      })
    }
    resetDeviceBinding()
    await loadOptions()
    await openDetail({ id: activeProjectId.value })
  } catch (error) {
    ElMessage.error(formatApiError(error, '绑定设备失败'))
  }
}

async function bindContract() {
  try {
    if (!activeProjectId.value || !selectedContractId.value) {
      ElMessage.warning('请选择要关联的合同')
      return
    }
    await createProjectContract({
      project: activeProjectId.value,
      contract: selectedContractId.value,
    })
    selectedContractId.value = null
    ElMessage.success('合同已关联')
    await openDetail({ id: activeProjectId.value })
  } catch (error) {
    ElMessage.error(formatApiError(error, '关联合同失败'))
  }
}

async function removeProjectContract(row) {
  try {
    await ElMessageBox.confirm(`确认解除合同“${row.contract_no}”？`, '解除确认', { type: 'warning' })
    await deleteProjectContract(row.id)
    ElMessage.success('合同关联已解除')
    await openDetail({ id: activeProjectId.value })
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(formatApiError(error, '解除合同关联失败'))
  }
}

watch(() => form.customer_org, async (customerOrgId) => {
  if (!dialogVisible.value) return
  await loadCustomerContacts(customerOrgId)
})

onMounted(async () => {
  await Promise.all([loadProjects(), loadOptions()])
})
</script>
