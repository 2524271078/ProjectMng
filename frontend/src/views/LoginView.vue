<template>
  <main class="login-page">
    <div class="login-art" aria-hidden="true"><i /><b /><em /></div>
    <section class="login-card" aria-labelledby="login-title">
      <h1 id="login-title">交付中台</h1>
      <el-form :model="form" @submit.prevent="submit">
        <el-form-item><el-input v-model="form.username" aria-label="用户名" autocomplete="username" placeholder="用户名" /></el-form-item>
        <el-form-item><el-input v-model="form.password" aria-label="密码" autocomplete="current-password" placeholder="密码" type="password" show-password /></el-form-item>
        <el-button type="primary" :loading="loading" class="login-button" @click="submit">登录</el-button>
      </el-form>
    </section>
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
