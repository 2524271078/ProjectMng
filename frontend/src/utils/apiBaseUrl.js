const LOCAL_DEV_API_BASE_URL = 'http://127.0.0.1:8000/api'

export function normalizeApiBaseUrl(value) {
  return String(value || '').trim().replace(/\/+$/, '')
}

export function resolveApiBaseUrl(env = {}, browserOrigin = "") {
  const configuredBaseUrl = normalizeApiBaseUrl(env.VITE_API_BASE_URL)
  if (configuredBaseUrl) return configuredBaseUrl

  if (env.DEV) return LOCAL_DEV_API_BASE_URL

  const normalizedOrigin = normalizeApiBaseUrl(browserOrigin)
  if (normalizedOrigin) return `${normalizedOrigin}/api`

  return LOCAL_DEV_API_BASE_URL
}
