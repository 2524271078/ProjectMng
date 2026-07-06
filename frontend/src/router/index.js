import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AdminLayout from '../layouts/AdminLayout.vue'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import CustomerCenterView from '../views/CustomerCenterView.vue'
import DeviceCenterView from '../views/DeviceCenterView.vue'
import DeviceDirectoryView from '../views/DeviceDirectoryView.vue'
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
    children: [
      { path: 'dashboard', component: DashboardView, meta: { title: '工作台' } },
      { path: 'customers', component: CustomerCenterView, meta: { title: '客户中心', menuCode: 'customers' } },
      { path: 'devices', component: DeviceCenterView, meta: { title: '项目中心', menuCode: 'devices' } },
      { path: 'device-center', component: DeviceDirectoryView, meta: { title: '设备中心', menuCode: 'device-center' } },
      { path: 'sales', component: SalesCenterView, meta: { title: '销售中心', menuCode: 'sales' } },
      { path: 'contracts', component: ContractCenterView, meta: { title: '合同中心', menuCode: 'contracts' } },
      { path: 'products', component: ProductModelView, meta: { title: '产品型号管理', menuCode: 'products' } },
      { path: 'people', component: PersonManageView, meta: { title: '人员管理', menuCode: 'people' } },
      { path: 'system', component: SystemManageView, meta: { title: '系统管理', menuCode: 'system' } },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.path !== '/login' && !auth.isAuthenticated) return '/login'
  if (to.path === '/login' && auth.isAuthenticated) return '/dashboard'
  if (auth.isAuthenticated && !auth.user) {
    await auth.loadCurrentUser()
  }
  const menuCode = to.meta?.menuCode
  if (menuCode && !auth.hasMenu(menuCode)) return '/dashboard'
})

export default router
