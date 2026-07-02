export function unwrapList(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}

export function formatApiError(error, fallback = '操作失败') {
  const data = error.response?.data
  if (!data || typeof data === 'string') return data || fallback
  return Object.entries(data).map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join('，') : messages}`).join('；')
}
