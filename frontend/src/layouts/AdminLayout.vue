<template>
  <div class="admin-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark"><img :src="brandLogo" alt="交付中台 Logo" /></span>
        <div>
          <strong>交付中台</strong>
          <small>Delivery Hub</small>
        </div>
      </div>
      <el-menu router :default-active="$route.path" class="side-menu">
        <el-menu-item v-for="item in visibleMenuItems" :key="item.index" :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
      <NotificationCenter />
    </aside>
    <main class="main-panel">
      <header class="topbar">
        <div>
          <h1>{{ $route.meta.title || '工作台' }}</h1>
        </div>
        <div class="topbar-actions">
          <div class="current-user" title="当前登录账号">
            <span>当前账号</span>
            <strong>{{ currentUserLabel }}</strong>
            <el-tag v-if="auth.isSuperuser" size="small" type="danger" effect="plain">超管</el-tag>
          </div>
          <el-button @click="handleLogout">退出</el-button>
        </div>
      </header>
      <section class="content-card">
        <router-view />
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Cpu,
  FolderOpened,
  HomeFilled,
  Monitor,
  OfficeBuilding,
  Setting,
  TrendCharts,
  User,
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import brandLogo from '../assets/brand-warrior.png'
import NotificationCenter from '../components/NotificationCenter.vue'

const router = useRouter()
const auth = useAuthStore()

const menuItems = [
  { index: '/dashboard', label: '工作台', icon: HomeFilled },
  { index: '/customers', label: '客户中心', code: 'customers', icon: OfficeBuilding },
  { index: '/devices', label: '项目中心', code: 'devices', icon: FolderOpened },
  { index: '/device-center', label: '设备中心', code: 'device-center', icon: Monitor },
  { index: '/sales', label: '销售中心', code: 'sales', icon: TrendCharts },
  { index: '/products', label: '设备型号', code: 'products', icon: Cpu },
  { index: '/people', label: '人员管理', code: 'people', icon: User },
  { index: '/system', label: '系统管理', code: 'system', icon: Setting },
]

const visibleMenuItems = computed(() => menuItems.filter((item) => auth.hasMenu(item.code)))
const currentUserLabel = computed(() => {
  const username = auth.user?.username || '未知账号'
  const personName = auth.user?.access_profile?.bound_person?.name
  return personName ? `${username}（${personName}）` : username
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.current-user {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 34px;
  padding: 0 10px;
  color: var(--app-subtle);
  font-size: 12px;
}

.current-user strong {
  color: var(--app-text);
  font-size: 13px;
  font-weight: 620;
}
</style>
