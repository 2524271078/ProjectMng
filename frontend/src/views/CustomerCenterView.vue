<template>
  <div class="split-page">
    <aside class="tree-panel">
      <div class="panel-title">组织树</div>
      <el-button type="primary" plain @click="loadOrganizations">刷新组织</el-button>
      <el-tree :data="treeData" node-key="id" :props="treeProps" default-expand-all @node-click="selectCustomer" />
    </aside>
    <section class="detail-panel">
      <div class="section-head">
        <div>
          <span class="eyebrow-dark">Customer Center</span>
          <h2>{{ selected?.name || '选择左侧客户' }}</h2>
        </div>
        <el-button type="primary" @click="dialogVisible = true">新增组织</el-button>
      </div>
      <el-tabs v-if="overview" model-value="base">
        <el-tab-pane label="客户详情" name="base"><el-descriptions :column="2" border><el-descriptions-item label="名称">{{ overview.customer.name }}</el-descriptions-item><el-descriptions-item label="类型">{{ overview.customer.org_type }}</el-descriptions-item><el-descriptions-item label="区域">{{ overview.customer.region || '-' }}</el-descriptions-item></el-descriptions></el-tab-pane>
        <el-tab-pane label="联系人" name="contacts"><el-table :data="overview.contacts"><el-table-column prop="name" label="姓名" /><el-table-column prop="phone" label="电话" /><el-table-column prop="email" label="邮箱" /></el-table></el-tab-pane>
        <el-tab-pane label="负责销售" name="sales"><el-table :data="overview.sales"><el-table-column prop="name" label="销售" /><el-table-column prop="phone" label="电话" /></el-table></el-tab-pane>
        <el-tab-pane label="已购设备" name="devices"><el-table :data="overview.devices"><el-table-column prop="name" label="设备" /><el-table-column prop="serial_number" label="序列号" /><el-table-column prop="status" label="状态" /></el-table></el-tab-pane>
        <el-tab-pane label="关联合同" name="contracts"><el-table :data="overview.contracts"><el-table-column prop="contract_no" label="合同编号" /><el-table-column prop="contract_name" label="合同名称" /><el-table-column prop="amount" label="金额" /></el-table></el-tab-pane>
      </el-tabs>
      <el-empty v-else description="请选择客户查看详情" />
    </section>
    <el-dialog v-model="dialogVisible" title="新增组织" width="460px">
      <el-form :model="form" label-width="90px"><el-form-item label="名称"><el-input v-model="form.name" /></el-form-item><el-form-item label="类型"><el-select v-model="form.org_type"><el-option label="客户" value="customer" /><el-option label="厂商" value="vendor" /><el-option label="集成商" value="integrator" /><el-option label="内部公司" value="internal_company" /></el-select></el-form-item><el-form-item label="区域"><el-input v-model="form.region" /></el-form-item></el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="createOrganization">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { createResource, fetchCustomerOverview, listResource } from '../api/resources'

const organizations = ref([])
const selected = ref(null)
const overview = ref(null)
const dialogVisible = ref(false)
const form = reactive({ name: '', org_type: 'customer', region: '' })
const treeProps = { label: 'name', children: 'children' }
const treeData = computed(() => organizations.value.map((item) => ({ ...item, children: [] })))

async function loadOrganizations() {
  const { data } = await listResource('organizations')
  organizations.value = data.results || data
}
async function selectCustomer(node) {
  selected.value = node
  const { data } = await fetchCustomerOverview(node.id)
  overview.value = data
}
async function createOrganization() {
  await createResource('organizations', form)
  dialogVisible.value = false
  Object.assign(form, { name: '', org_type: 'customer', region: '' })
  await loadOrganizations()
}
onMounted(loadOrganizations)
</script>
