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
        <el-button type="primary" @click="openCreateDialog">新增组织</el-button>
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
          <el-table :data="overview.contacts"><el-table-column prop="name" label="姓名" /><el-table-column prop="phone" label="电话" /><el-table-column prop="email" label="邮箱" /></el-table>
        </el-tab-pane>
        <el-tab-pane label="负责销售" name="sales">
          <el-table :data="overview.sales"><el-table-column prop="name" label="销售" /><el-table-column prop="phone" label="电话" /></el-table>
        </el-tab-pane>
        <el-tab-pane label="已购设备" name="devices">
          <el-table :data="overview.devices"><el-table-column prop="name" label="设备" /><el-table-column prop="serial_number" label="序列号" /><el-table-column prop="status" label="状态" /></el-table>
        </el-tab-pane>
        <el-tab-pane label="关联合同" name="contracts">
          <el-table :data="overview.contracts"><el-table-column prop="contract_no" label="合同编号" /><el-table-column prop="contract_name" label="合同名称" /><el-table-column prop="amount" label="金额" /></el-table>
        </el-tab-pane>
      </el-tabs>
      <el-empty v-else description="请选择客户查看详情" />
    </section>

    <el-dialog v-model="dialogVisible" title="新增组织" width="520px">
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
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import OrganizationTreeSelect from '../components/OrganizationTreeSelect.vue'
import { createResource, fetchCustomerOverview, listResource } from '../api/resources'
import { buildOrganizationTree } from '../utils/orgTree'

const organizations = ref([])
const selected = ref(null)
const overview = ref(null)
const dialogVisible = ref(false)
const saving = ref(false)
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

function openCreateDialog() {
  form.parent = selected.value?.id || null
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
    await createResource('organizations', buildPayload())
    ElMessage.success('组织已新增')
    dialogVisible.value = false
    resetForm()
    await loadOrganizations()
  } catch (error) {
    ElMessage.error('保存组织失败，请检查必填项')
  } finally {
    saving.value = false
  }
}

onMounted(loadOrganizations)
</script>
