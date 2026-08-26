<template>
  <main class="license-locked-page">
    <section class="license-locked-card">
      <div class="license-locked-card__mark"><el-icon><Lock /></el-icon></div>
      <p class="license-locked-card__eyebrow">系统访问受限</p>
      <h1>系统授权已到期或无效</h1>
      <p>当前系统暂不可使用，请联系授权管理员续期后恢复访问。</p>
      <div class="license-locked-card__actions">
        <el-button v-if="auth.isLicenseOperator" type="primary" @click="router.push('/license')">进入授权管理</el-button>
        <el-button v-else @click="router.push('/login')">返回登录页</el-button>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted } from 'vue'
import { Lock } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

onMounted(async () => {
  if (auth.isAuthenticated && !auth.user) {
    try {
      await auth.loadCurrentUser()
    } catch {
      auth.logout()
    }
  }
})
</script>

<style scoped>
.license-locked-page { display: grid; min-height: 100vh; place-items: center; padding: 32px; background: #f5f8fc; }
.license-locked-card { width: min(100%, 480px); padding: 52px; border: 1px solid var(--app-border); border-radius: 20px; background: #fff; box-shadow: 0 18px 48px rgb(39 68 112 / 10%); text-align: center; }
.license-locked-card__mark { display: grid; width: 56px; height: 56px; margin: 0 auto 22px; place-items: center; border-radius: 18px; background: #fff1f1; color: var(--app-danger); font-size: 27px; }
.license-locked-card__eyebrow { margin: 0 0 10px; color: var(--app-primary); font-size: 13px; font-weight: 700; letter-spacing: .08em; }
.license-locked-card h1 { margin: 0; color: var(--app-ink); font-size: 25px; }
.license-locked-card > p:not(.license-locked-card__eyebrow) { margin: 16px 0 26px; color: var(--app-text); line-height: 1.8; }
</style>
