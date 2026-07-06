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

export function login(payload) {
  return apiClient.post('/auth/login/', payload)
}

export function fetchMe() {
  return apiClient.get('/auth/me/')
}

