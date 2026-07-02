import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AdminLayout from '../layouts/AdminLayout.vue'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import CustomerCenterView from '../views/CustomerCenterView.vue'
import DeviceCenterView from '../views/DeviceCenterView.vue'
import SalesCenterView from '../views/SalesCenterView.vue'
import ContractCenterView from '../views/ContractCenterView.vue'
import ProductModelView from '../views/ProductModelView.vue'
import PersonManageView from '../views/PersonManageView.vue'
import SystemManageView from '../views/SystemManageView.vue'

const routes = [
  { path: '/login', component: LoginView },
  {
    path: '/',
    component: AdminLayout,
    redirect: '/dashboard',
    children: [{ path: 'dashboard', component: DashboardView, meta: { title: '工作台' } },
      { path: 'customers', component: CustomerCenterView, meta: { title: '客户中心' } },
      { path: 'devices', component: DeviceCenterView, meta: { title: '设备中心' } },
      { path: 'sales', component: SalesCenterView, meta: { title: '销售中心' } },
      { path: 'contracts', component: ContractCenterView, meta: { title: '合同中心' } },
      { path: 'products', component: ProductModelView, meta: { title: '产品型号管理' } },
      { path: 'people', component: PersonManageView, meta: { title: '人员管理' } },
      { path: 'system', component: SystemManageView, meta: { title: '系统管理' } }],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.path !== '/login' && !auth.isAuthenticated) return '/login'
  if (to.path === '/login' && auth.isAuthenticated) return '/dashboard'
})

export default router
