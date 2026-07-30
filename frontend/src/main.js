import { createApp } from 'vue'
import ElementPlus from 'element-plus'
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
app.use(router).use(ElementPlus).mount('#app')
