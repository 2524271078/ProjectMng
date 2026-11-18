export function unwrapList(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}

export function formatApiError(error, fallback = '操作失败') {
  const data = error.response?.data
  if (!data) return fallback
  if (typeof data === 'string') {
    const message = data.trim()
    if (!message || /<(?:!DOCTYPE|html|head|body)\b/i.test(message)) return fallback
    return message.length > 300 ? `${message.slice(0, 300)}…` : message
  }
  return Object.entries(data).map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join('，') : messages}`).join('；')
}
