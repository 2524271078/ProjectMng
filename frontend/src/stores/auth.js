import { defineStore } from 'pinia'
import { fetchMe, login } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: localStorage.getItem('pm_token') || '', user: null, menus: [] }),
  getters: { isAuthenticated: (state) => Boolean(state.token) },
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
    },
    logout() {
      this.token = ''
      this.user = null
      this.menus = []
      localStorage.removeItem('pm_token')
    },
  },
})
