<template>
  <div class="admin-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">PM</span>
        <div>
          <strong>项目设备管理</strong>
          <small>Project Ops</small>
        </div>
      </div>
      <el-menu router :default-active="$route.path" class="side-menu">
        <el-menu-item index="/dashboard">工作台</el-menu-item>
        <el-menu-item index="/customers">客户中心</el-menu-item>
        <el-menu-item index="/devices">项目中心</el-menu-item>
        <el-menu-item index="/device-center">设备中心</el-menu-item>
        <el-menu-item index="/sales">销售中心</el-menu-item>
        <el-menu-item index="/contracts">合同中心</el-menu-item>
        <el-menu-item index="/products">产品型号</el-menu-item>
        <el-menu-item index="/people">人员管理</el-menu-item>
        <el-menu-item index="/system">系统管理</el-menu-item>
      </el-menu>
    </aside>
    <main class="main-panel">
      <header class="topbar">
        <div>
          <h1>{{ $route.meta.title || '工作台' }}</h1>
          <p>销售、客户、设备、合同链路统一维护</p>
        </div>
        <el-button @click="handleLogout">退出</el-button>
      </header>
      <section class="content-card">
        <router-view />
      </section>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
