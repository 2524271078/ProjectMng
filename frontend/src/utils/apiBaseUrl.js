const LOCAL_DEV_API_BASE_URL = 'http://127.0.0.1:8000/api'

export function normalizeApiBaseUrl(value) {
  return String(value || '').trim().replace(/\/+$/, '')
}

function isLoopbackUrl(value) {
  try {
    const hostname = new URL(value).hostname
    return hostname === '127.0.0.1' || hostname === 'localhost' || hostname === '::1'
  } catch {
    return false
  }
}

export function resolveApiBaseUrl(env = {}, browserOrigin = "") {
  const configuredBaseUrl = normalizeApiBaseUrl(env.VITE_API_BASE_URL)
  const normalizedOrigin = normalizeApiBaseUrl(browserOrigin)

  // `.env.local` is loaded by Vite for production builds too. Never let a
  // loopback-only development setting send an intranet deployment back to the
  // visitor's own computer.
  const unsafeProductionLoopback =
    !env.DEV &&
    configuredBaseUrl &&
    isLoopbackUrl(configuredBaseUrl) &&
    normalizedOrigin &&
    !isLoopbackUrl(normalizedOrigin)

  if (configuredBaseUrl && !unsafeProductionLoopback) return configuredBaseUrl

  if (env.DEV) return LOCAL_DEV_API_BASE_URL

  if (normalizedOrigin) return `${normalizedOrigin}/api`

  return LOCAL_DEV_API_BASE_URL
}
