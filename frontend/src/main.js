import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import './styles/main.css'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.directive('can', {
  mounted(el, binding) {
    const [menuCode, action = 'view'] = binding.value || []
    if (!useAuthStore(pinia).hasAction(menuCode, action)) el.remove()
  },
  updated(el, binding) {
    const [menuCode, action = 'view'] = binding.value || []
    if (!useAuthStore(pinia).hasAction(menuCode, action)) el.remove()
  },
})
app.use(router).use(ElementPlus, { locale: zhCn }).mount('#app')
