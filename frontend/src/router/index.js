import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AdminLayout from '../layouts/AdminLayout.vue'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import CustomerCenterView from '../views/CustomerCenterView.vue'
import DeviceCenterView from '../views/DeviceCenterView.vue'

const routes = [
  { path: '/login', component: LoginView },
  {
    path: '/',
    component: AdminLayout,
    redirect: '/dashboard',
    children: [{ path: 'dashboard', component: DashboardView, meta: { title: '工作台' } },
      { path: 'customers', component: CustomerCenterView, meta: { title: '客户中心' } },
      { path: 'devices', component: DeviceCenterView, meta: { title: '设备中心' } }],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.path !== '/login' && !auth.isAuthenticated) return '/login'
  if (to.path === '/login' && auth.isAuthenticated) return '/dashboard'
})

export default router
