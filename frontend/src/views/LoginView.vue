<template>
  <main class="login-page">
    <section class="login-hero">
      <span class="eyebrow">Delivery Hub</span>
      <h1>交付中台</h1>
      <p>客户、项目、设备、合同统一协同，支撑交付全过程管理。</p>
    </section>
    <el-card class="login-card" shadow="never">
      <h2>登录交付中台</h2>
      <el-form :model="form" @submit.prevent="submit">
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
        <el-button type="primary" :loading="loading" class="login-button" @click="submit">登录</el-button>
      </el-form>
    </el-card>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

onMounted(() => {
  if (route.query.reason === 'timeout') ElMessage.warning('登录超时，请重新登录')
})

async function submit() {
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>
