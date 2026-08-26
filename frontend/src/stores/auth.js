import { defineStore } from 'pinia'
import { fetchMe, login } from '../api/client'
import { buildMenuCodeSet, hasActionAccess, hasMenuAccess } from '../utils/authz'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('pm_token') || '',
    user: null,
    menus: [],
    permissions: [],
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    isSuperuser: (state) => Boolean(state.user?.is_superuser),
    isLicenseOperator: (state) => state.user?.username === 'xushaotai',
    menuCodes: (state) => buildMenuCodeSet(state.menus),
  },
  actions: {
    async login(username, password) {
      const { data } = await login({ username, password })
      this.token = data.token
      this.user = data.user
      localStorage.setItem('pm_token', data.token)
      await this.loadCurrentUser()
    },
    async loadCurrentUser() {
      if (!this.token) return
      const { data } = await fetchMe()
      this.user = data
      this.menus = data.menus || []
      this.permissions = data.permissions || []
    },
    hasMenu(code) {
      return hasMenuAccess({ isSuperuser: this.isSuperuser, menuCodes: this.menuCodes }, code)
    },
    hasAction(menuCode, action = 'view') {
      return hasActionAccess({ isSuperuser: this.isSuperuser, permissions: this.permissions }, menuCode, action)
    },
    logout() {
      this.token = ''
      this.user = null
      this.menus = []
      this.permissions = []
      localStorage.removeItem('pm_token')
    },
  },
})
