import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  timeout: 15000,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('pm_token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

export function login(payload) {
  return apiClient.post('/auth/login/', payload)
}

export function fetchMe() {
  return apiClient.get('/auth/me/')
}
