<template>
  <main class="license-manage page-scroll-layout">
    <div class="page-scroll-body license-manage__body">
      <section class="license-manage__intro">
        <p>LICENSE CONTROL</p>
        <h2>系统授权</h2>
        <span>授权文件仅可由系统所有者签发，当前入口仅对指定账号开放。</span>
      </section>

      <el-card class="license-card" shadow="never" v-loading="loading">
        <template #header><div class="license-card__title"><span>当前状态</span><el-tag :type="statusTagType" effect="light">{{ statusText }}</el-tag></div></template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="授权客户">{{ licensePayload.customer || '未授权' }}</el-descriptions-item>
          <el-descriptions-item label="授权编号">{{ licensePayload.license_id || '—' }}</el-descriptions-item>
          <el-descriptions-item label="有效期至">{{ licensePayload.expires_at || '—' }}</el-descriptions-item>
          <el-descriptions-item label="设备指纹"><span class="license-fingerprint">{{ statusData.machine_fingerprint || '—' }}</span></el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="license-card" shadow="never">
        <template #header><div class="license-card__title"><span>续期与激活</span></div></template>
        <div class="license-activate">
          <div>
            <h3>先生成授权请求文件</h3>
            <p>将请求文件发送给系统所有者，由其离线签发新的授权文件。</p>
          </div>
          <el-button @click="downloadRequest">下载授权请求</el-button>
        </div>
        <el-divider />
        <div class="license-activate">
          <div>
            <h3>上传已签名授权文件</h3>
            <p>仅接受由系统所有者签发的 <code>.lic</code> 或 JSON 授权文件。</p>
          </div>
          <el-upload :show-file-list="false" accept=".lic,.json,application/json" :auto-upload="false" :on-change="handleFileChange">
            <el-button type="primary">上传并激活</el-button>
          </el-upload>
        </div>
      </el-card>
    </div>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { activateLicense, fetchLicenseRequest, fetchLicenseStatus } from '../api/resources'
import { formatApiError } from '../utils/apiData'

const loading = ref(false)
const statusData = ref({})
const licensePayload = computed(() => statusData.value.payload || {})
const statusText = computed(() => statusData.value.active ? '授权有效' : '未授权 / 已失效')
const statusTagType = computed(() => statusData.value.active ? 'success' : 'danger')

async function loadStatus() {
  loading.value = true
  try {
    const { data } = await fetchLicenseStatus()
    statusData.value = data
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载授权状态失败'))
  } finally {
    loading.value = false
  }
}

async function downloadRequest() {
  try {
    const { data } = await fetchLicenseRequest()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = '交付中台-授权请求.json'
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error(formatApiError(error, '生成授权请求失败'))
  }
}

async function handleFileChange(uploadFile) {
  try {
    const content = await uploadFile.raw.text()
    const { data } = await activateLicense(JSON.parse(content))
    statusData.value = data
    ElMessage.success('授权文件已验证并生效')
  } catch (error) {
    ElMessage.error(formatApiError(error, '授权文件无效或激活失败'))
  }
}

onMounted(loadStatus)
</script>

<style scoped>
.license-manage__body { width: min(100%, 980px); margin: 0 auto; padding: 34px; }
.license-manage__intro { margin: 0 0 24px; }
.license-manage__intro p { margin: 0 0 8px; color: var(--app-primary); font-size: 12px; font-weight: 700; letter-spacing: .1em; }
.license-manage__intro h2 { margin: 0; color: var(--app-ink); font-size: 28px; letter-spacing: -.03em; }
.license-manage__intro span { display: block; margin-top: 9px; color: var(--app-text); font-size: 14px; }
.license-card + .license-card { margin-top: 16px; }
.license-card__title { display: flex; align-items: center; justify-content: space-between; color: var(--app-ink); font-weight: 680; }
.license-fingerprint { font-family: Inter, monospace; font-size: 12px; word-break: break-all; }
.license-activate { display: flex; align-items: center; justify-content: space-between; gap: 24px; }
.license-activate h3 { margin: 0; color: var(--app-ink); font-size: 15px; }
.license-activate p { margin: 7px 0 0; color: var(--app-text); font-size: 13px; }
@media (max-width: 720px) { .license-manage__body { padding: 22px 16px; } .license-activate { align-items: flex-start; flex-direction: column; gap: 14px; } }
</style>
