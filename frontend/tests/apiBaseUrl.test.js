import test from 'node:test'
import assert from 'node:assert/strict'
import { normalizeApiBaseUrl, resolveApiBaseUrl } from '../src/utils/apiBaseUrl.js'

test('normalizeApiBaseUrl 会去掉末尾斜杠', () => {
  assert.equal(normalizeApiBaseUrl('http://192.168.1.10:8000/api/'), 'http://192.168.1.10:8000/api')
  assert.equal(normalizeApiBaseUrl('http://192.168.1.10:8000/api'), 'http://192.168.1.10:8000/api')
})

test('resolveApiBaseUrl 优先使用环境变量', () => {
  const result = resolveApiBaseUrl({ VITE_API_BASE_URL: 'http://192.168.1.20:8000/api/' }, 'http://192.168.1.20:5173')
  assert.equal(result, 'http://192.168.1.20:8000/api')
})

test('resolveApiBaseUrl 在开发环境回退到本地后端', () => {
  const result = resolveApiBaseUrl({ DEV: true }, 'http://192.168.1.20:5173')
  assert.equal(result, 'http://127.0.0.1:8000/api')
})

test('resolveApiBaseUrl 在生产环境默认使用当前来源', () => {
  const result = resolveApiBaseUrl({ DEV: false }, 'http://192.168.1.20:8080')
  assert.equal(result, 'http://192.168.1.20:8080/api')
})
