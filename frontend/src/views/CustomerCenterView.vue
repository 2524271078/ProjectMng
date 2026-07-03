<template>
  <div class="split-page">
    <aside class="tree-panel">
      <div class="panel-title">组织树</div>
      <el-button type="primary" plain @click="loadOrganizations">刷新组织</el-button>
      <el-tree
        :data="treeData"
        node-key="id"
        :props="treeProps"
        default-expand-all
        highlight-current
        @node-click="selectCustomer"
      />
    </aside>

    <section class="detail-panel">
      <div class="section-head">
        <div>
          <span class="eyebrow-dark">Customer Center</span>
          <h2>{{ selected?.name || '选择左侧客户' }}</h2>
        </div>
        <div class="action-row">
          <el-button @click="openEditDialog" :disabled="!selected">编辑组织</el-button>
          <el-button type="danger" plain @click="removeOrganization" :disabled="!selected">删除组织</el-button>
          <el-button type="primary" @click="openCreateDialog">新增组织</el-button>
        </div>
      </div>

      <el-tabs v-if="overview" model-value="base">
        <el-tab-pane label="客户详情" name="base">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="名称">{{ overview.customer.name }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ overview.customer.org_type }}</el-descriptions-item>
            <el-descriptions-item label="区域">{{ overview.customer.region || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
        <el-tab-pane label="联系人" name="contacts">
          <el-table :data="overview.contacts">
            <el-table-column prop="name" label="姓名" />
            <el-table-column prop="position" label="职位" />
            <el-table-column prop="phone" label="电话" />
            <el-table-column prop="email" label="邮箱" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="负责销售" name="sales">
          <el-table :data="overview.sales">
            <el-table-column prop="name" label="销售" />
            <el-table-column prop="phone" label="电话" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="已购设备" name="devices">
          <el-table :data="overview.devices">
            <el-table-column prop="name" label="设备" />
            <el-table-column prop="serial_number" label="序列号" />
            <el-table-column prop="status" label="状态" />
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button link type="primary" @click.stop="openDeviceDetail(scope.row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="关联合同" name="contracts">
          <el-table :data="overview.contracts">
            <el-table-column prop="contract_no" label="合同编号" />
            <el-table-column prop="contract_name" label="合同名称" />
            <el-table-column prop="amount" label="金额" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="关联项目" name="projects">
          <el-table :data="overview.projects || []" @row-click="openProjectDetail">
            <el-table-column prop="project_no" label="项目编号" min-width="150" />
            <el-table-column prop="name" label="项目名称" min-width="220" />
            <el-table-column prop="project_stage" label="阶段" min-width="120" />
            <el-table-column label="销售" min-width="120">
              <template #default="scope">{{ scope.row.sales_person?.name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" min-width="120" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
      <el-empty v-else description="请选择客户查看详情" />
    </section>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑组织' : '新增组织'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="上级组织">
          <OrganizationTreeSelect v-model="form.parent" placeholder="不选则作为根组织" />
        </el-form-item>
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.org_type">
            <el-option label="客户" value="customer" />
            <el-option label="厂商" value="vendor" />
            <el-option label="集成商" value="integrator" />
            <el-option label="内部公司" value="internal_company" />
            <el-option label="第三方中标单位" value="third_party_bidder" />
          </el-select>
        </el-form-item>
        <el-form-item label="简称"><el-input v-model="form.short_name" /></el-form-item>
        <el-form-item label="区域"><el-input v-model="form.region" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="createOrganization">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="projectDrawerVisible" size="68%" title="项目详情">
      <el-tabs v-if="projectOverview" model-value="base">
        <el-tab-pane label="基础信息" name="base">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目编号">{{ projectOverview.project.project_no }}</el-descriptions-item>
            <el-descriptions-item label="项目名称">{{ projectOverview.project.name }}</el-descriptions-item>
            <el-descriptions-item label="客户公司">{{ projectOverview.customer?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="客户联系人">{{ projectOverview.customer_contact?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="联系人职位">{{ projectOverview.customer_contact?.position || '-' }}</el-descriptions-item>
            <el-descriptions-item label="实际中标公司">{{ projectOverview.project.winning_company || '-' }}</el-descriptions-item>
            <el-descriptions-item label="对接公司">{{ projectOverview.project.contact_company || '-' }}</el-descriptions-item>
            <el-descriptions-item label="销售">{{ projectOverview.sales_person?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="阶段">{{ projectOverview.project.project_stage || '-' }}</el-descriptions-item>
            <el-descriptions-item label="金额">{{ projectOverview.project.amount }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <el-tab-pane label="项目设备" name="devices">
          <el-table :data="projectOverview.devices || []" stripe>
            <el-table-column prop="name" label="设备" min-width="160" />
            <el-table-column prop="serial_number" label="序列号" min-width="160" />
            <el-table-column prop="device_project_type" label="项目类型" min-width="120" />
            <el-table-column prop="management_address" label="管理地址" min-width="180" />
            <el-table-column label="现场运维" min-width="120">
              <template #default="scope">{{ scope.row.ops_person?.name || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button link type="primary" @click.stop="openDeviceDetail(scope.row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="关联合同" name="contracts">
          <el-table :data="projectOverview.contracts || []" stripe>
            <el-table-column prop="contract_no" label="合同编号" min-width="150" />
            <el-table-column prop="contract_name" label="合同名称" min-width="220" />
            <el-table-column prop="amount" label="金额" min-width="120" />
            <el-table-column prop="status" label="状态" min-width="120" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="项目附件" name="attachments">
          <el-table :data="projectOverview.attachments || []" stripe>
            <el-table-column prop="name" label="附件名" />
            <el-table-column prop="uploaded_at" label="上传时间" />
            <el-table-column label="操作" width="160">
              <template #default="scope">
                <el-button v-if="scope.row.file_url" link type="primary" @click="previewAttachment(scope.row)">预览</el-button>
                <el-button v-if="scope.row.file_url" link type="primary" @click="downloadAttachment(scope.row)">下载</el-button>
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
        <el-descriptions-item label="上架时间">{{ selectedDevice.rack_install_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="是否标品">{{ selectedDevice.is_standard_product ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="是否支持远程">{{ selectedDevice.supports_remote ? '支持' : '不支持' }}</el-descriptions-item>
        <el-descriptions-item label="是否保内">{{ selectedDevice.is_under_warranty ? '保内' : '保外' }}</el-descriptions-item>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import OrganizationTreeSelect from '../components/OrganizationTreeSelect.vue'
import { createResource, deleteResource, fetchCustomerOverview, fetchProjectOverview, listResource, updateResource } from '../api/resources'
import { buildOrganizationTree } from '../utils/orgTree'

const organizations = ref([])
const selected = ref(null)
const overview = ref(null)
const projectDrawerVisible = ref(false)
const projectOverview = ref(null)
const deviceDetailVisible = ref(false)
const selectedDevice = ref(null)
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const form = reactive({ parent: null, name: '', org_type: 'customer', short_name: '', region: '', address: '' })
const treeProps = { label: 'name', children: 'children' }
const treeData = computed(() => buildOrganizationTree(organizations.value))

async function loadOrganizations() {
  const { data } = await listResource('organizations')
  organizations.value = data.results || data
}

async function selectCustomer(node) {
  selected.value = node
  const { data } = await fetchCustomerOverview(node.id)
  overview.value = data
}

async function openProjectDetail(row) {
  const { data } = await fetchProjectOverview(row.id)
  projectOverview.value = data
  projectDrawerVisible.value = true
}

function openDeviceDetail(device) {
  selectedDevice.value = device
  deviceDetailVisible.value = true
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

function openCreateDialog() {
  editingId.value = null
  resetForm()
  form.parent = selected.value?.id || null
  dialogVisible.value = true
}

function openEditDialog() {
  if (!selected.value) return
  editingId.value = selected.value.id
  Object.assign(form, {
    parent: selected.value.parent || null,
    name: selected.value.name || '',
    org_type: selected.value.org_type || 'customer',
    short_name: selected.value.short_name || '',
    region: selected.value.region || '',
    address: selected.value.address || '',
  })
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(form, { parent: null, name: '', org_type: 'customer', short_name: '', region: '', address: '' })
}

function buildPayload() {
  const payload = { ...form }
  if (!payload.parent) delete payload.parent
  return payload
}

async function createOrganization() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写组织名称')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateResource('organizations', editingId.value, buildPayload())
    } else {
      await createResource('organizations', buildPayload())
    }
    ElMessage.success(editingId.value ? '组织已更新' : '组织已新增')
    dialogVisible.value = false
    resetForm()
    editingId.value = null
    await loadOrganizations()
  } catch (error) {
    ElMessage.error('保存组织失败，请检查必填项')
  } finally {
    saving.value = false
  }
}

async function removeOrganization() {
  if (!selected.value) return
  await ElMessageBox.confirm(`确认删除组织“${selected.value.name}”？`, '删除确认', { type: 'warning' })
  await deleteResource('organizations', selected.value.id)
  ElMessage.success('组织已删除')
  selected.value = null
  overview.value = null
  projectOverview.value = null
  projectDrawerVisible.value = false
  await loadOrganizations()
}

onMounted(loadOrganizations)
</script>
