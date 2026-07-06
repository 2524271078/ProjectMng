<template>
  <div class="admin-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">PM</span>
        <div>
          <strong>交付中台</strong>
          <small>Delivery Hub</small>
        </div>
      </div>
      <el-menu router :default-active="$route.path" class="side-menu">
        <el-menu-item v-for="item in visibleMenuItems" :key="item.index" :index="item.index">{{ item.label }}</el-menu-item>
      </el-menu>
    </aside>
    <main class="main-panel">
      <header class="topbar">
        <div>
          <h1>{{ $route.meta.title || '工作台' }}</h1>
          <p>客户、项目、设备、合同统一协同</p>
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const menuItems = [
  { index: '/dashboard', label: '工作台' },
  { index: '/customers', label: '客户中心', code: 'customers' },
  { index: '/devices', label: '项目中心', code: 'devices' },
  { index: '/device-center', label: '设备中心', code: 'device-center' },
  { index: '/sales', label: '销售中心', code: 'sales' },
  { index: '/contracts', label: '合同中心', code: 'contracts' },
  { index: '/products', label: '产品型号', code: 'products' },
  { index: '/people', label: '人员管理', code: 'people' },
  { index: '/system', label: '系统管理', code: 'system' },
]

const visibleMenuItems = computed(() => menuItems.filter((item) => auth.hasMenu(item.code)))

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
