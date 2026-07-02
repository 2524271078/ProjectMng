<template>
  <div>
    <div class="section-head"><div><span class="eyebrow-dark">Device Center</span><h2>设备资产</h2></div><el-button type="primary" @click="dialogVisible = true">新增设备</el-button></div>
    <el-table :data="devices" stripe @row-click="openDetail">
      <el-table-column prop="name" label="设备名称" min-width="180" />
      <el-table-column prop="serial_number" label="序列号" min-width="160" />
      <el-table-column prop="software_version" label="软件版本" />
      <el-table-column prop="rule_library_version" label="规则库版本" />
      <el-table-column prop="status" label="状态" />
    </el-table>
    <el-dialog v-model="dialogVisible" title="新增设备" width="560px">
      <el-form :model="form" label-width="120px"><el-form-item label="设备名称"><el-input v-model="form.name" /></el-form-item><el-form-item label="序列号"><el-input v-model="form.serial_number" /></el-form-item><el-form-item label="设备型号 ID"><el-input-number v-model="form.device_model" :min="1" /></el-form-item><el-form-item label="客户组织 ID"><el-input-number v-model="form.customer_org" :min="1" /></el-form-item><el-form-item label="销售人员 ID"><el-input-number v-model="form.sales_person" :min="1" /></el-form-item></el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="createDevice">保存</el-button></template>
    </el-dialog>
    <el-drawer v-model="drawerVisible" size="52%" title="设备详情">
      <el-tabs v-if="overview" model-value="base">
        <el-tab-pane label="基础信息" name="base"><el-descriptions :column="2" border><el-descriptions-item label="名称">{{ overview.device.name }}</el-descriptions-item><el-descriptions-item label="序列号">{{ overview.device.serial_number }}</el-descriptions-item><el-descriptions-item label="硬件编码">{{ overview.device.hardware_code || '-' }}</el-descriptions-item><el-descriptions-item label="状态">{{ overview.device.status }}</el-descriptions-item></el-descriptions></el-tab-pane>
        <el-tab-pane label="授权信息" name="license"><pre class="json-box">{{ overview.device.license_info }}</pre></el-tab-pane>
        <el-tab-pane label="合同信息" name="contracts"><el-table :data="overview.contracts"><el-table-column prop="contract_no" label="合同编号" /><el-table-column prop="contract_name" label="合同名称" /><el-table-column prop="amount" label="金额" /></el-table></el-tab-pane>
        <el-tab-pane label="客户信息" name="customer"><el-descriptions v-if="overview.customer" border><el-descriptions-item label="客户">{{ overview.customer.name }}</el-descriptions-item><el-descriptions-item label="销售">{{ overview.sales_person?.name || '-' }}</el-descriptions-item><el-descriptions-item label="运维">{{ overview.ops_person?.name || '-' }}</el-descriptions-item></el-descriptions></el-tab-pane>
        <el-tab-pane label="图片附件" name="attachments"><el-upload drag action="#" :auto-upload="false"><el-icon><UploadFilled /></el-icon><div>拖拽图片到此处，后续接入附件上传 API</div></el-upload><el-table :data="overview.attachments"><el-table-column prop="name" label="附件名" /></el-table></el-tab-pane>
      </el-tabs>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { createResource, fetchDeviceOverview, listResource } from '../api/resources'

const devices = ref([])
const overview = ref(null)
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const form = reactive({ name: '', serial_number: '', device_model: 1, customer_org: undefined, sales_person: undefined })
async function loadDevices() { const { data } = await listResource('devices'); devices.value = data.results || data }
async function createDevice() { await createResource('devices', form); dialogVisible.value = false; await loadDevices() }
async function openDetail(row) { const { data } = await fetchDeviceOverview(row.id); overview.value = data; drawerVisible.value = true }
onMounted(loadDevices)
</script>
