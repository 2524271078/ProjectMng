<template>
  <el-descriptions v-if="device" :column="column" border>
    <el-descriptions-item label="设备名称">{{ device.name || '-' }}</el-descriptions-item>
    <el-descriptions-item label="序列号">{{ device.serial_number || '-' }}</el-descriptions-item>
    <el-descriptions-item v-if="customerName" label="客户公司">{{ customerName }}</el-descriptions-item>
    <el-descriptions-item label="产品型号">{{ device.device_model_detail?.model_name || '-' }}</el-descriptions-item>
    <el-descriptions-item label="管理地址">{{ device.management_address || '-' }}</el-descriptions-item>
    <el-descriptions-item label="设备硬件码">{{ device.hardware_code || '-' }}</el-descriptions-item>
    <el-descriptions-item label="设备系统版本">{{ device.software_version || '-' }}</el-descriptions-item>
    <el-descriptions-item label="版本更新方式">{{ device.version_update_method || '-' }}</el-descriptions-item>
    <el-descriptions-item label="合同开始">{{ contractStartDate }}</el-descriptions-item>
    <el-descriptions-item label="合同结束">{{ contractEndDate }}</el-descriptions-item>
    <el-descriptions-item label="保内状态">{{ serviceStatus }}</el-descriptions-item>
    <el-descriptions-item label="上架时间">{{ device.rack_install_date || '-' }}</el-descriptions-item>
    <el-descriptions-item label="是否标品">{{ standardProductLabel }}</el-descriptions-item>
    <el-descriptions-item v-if="showNonstandardName" label="非标名称">{{ device.nonstandard_name || '-' }}</el-descriptions-item>
    <el-descriptions-item label="是否支持远程">{{ supportsRemoteLabel }}</el-descriptions-item>
    <el-descriptions-item label="部署位置">{{ device.deploy_location || '-' }}</el-descriptions-item>
    <el-descriptions-item label="截图链接">
      <a v-if="device.screenshot_url" :href="device.screenshot_url" target="_blank" rel="noopener noreferrer">预览</a>
      <span v-else>-</span>
    </el-descriptions-item>
    <el-descriptions-item label="备注" :span="2">{{ device.remark || '-' }}</el-descriptions-item>
  </el-descriptions>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  device: {
    type: Object,
    default: null,
  },
  column: {
    type: Number,
    default: 2,
  },
})

const customerName = computed(() => props.device?.customer?.name || props.device?.customer_org_detail?.name || '')
const contractStartDate = computed(() => props.device?.service_start_date || props.device?.current_service_start_date || '-')
const contractEndDate = computed(() => props.device?.service_end_date || props.device?.current_service_end_date || '-')
const serviceStatus = computed(() => props.device?.service_status || props.device?.current_service_status || '-')
const showNonstandardName = computed(() => props.device && props.device.is_standard_product === false)
const standardProductLabel = computed(() => (props.device?.is_standard_product ? '是' : '否'))
const supportsRemoteLabel = computed(() => (props.device?.supports_remote ? '支持' : '不支持'))
</script>
