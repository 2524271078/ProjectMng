import axios from 'axios'
import { resolveApiBaseUrl } from '../utils/apiBaseUrl'

export const apiClient = axios.create({
  baseURL: resolveApiBaseUrl(import.meta.env, typeof window !== 'undefined' ? window.location.origin : ''),
  timeout: 15000,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('pm_token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config?.url?.includes('/auth/login/')
    if (error.response?.status === 401 && !isLoginRequest && typeof window !== 'undefined') {
      localStorage.removeItem('pm_token')
      if (!window.location.pathname.startsWith('/login')) window.location.assign('/login?reason=timeout')
    }
    return Promise.reject(error)
  },
)

export function login(payload) {
  return apiClient.post('/auth/login/', payload)
}

export function fetchMe() {
  return apiClient.get('/auth/me/')
}

