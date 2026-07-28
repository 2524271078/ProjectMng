import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync(new URL('../src/components/DeviceServiceWorkspace.vue', import.meta.url), 'utf8')

test('设备服务页仅展示具体服务项，不展示服务计划总览表', () => {
  assert.equal(source.includes(':data="plans"'), false)
  assert.equal(source.includes(':data="schedules"'), true)
  assert.equal(source.includes('当前服务计划暂无服务项，请新增服务项'), true)
})
