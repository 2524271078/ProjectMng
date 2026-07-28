import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync(new URL('../src/components/DeviceServiceWorkspace.vue', import.meta.url), 'utf8')
const deviceDirectorySource = readFileSync(new URL('../src/views/DeviceDirectoryView.vue', import.meta.url), 'utf8')

test('设备服务页仅展示具体服务项，不展示服务计划总览表', () => {
  assert.equal(source.includes(':data="plans"'), false)
  assert.equal(source.includes(':data="schedules"'), true)
  assert.equal(source.includes('当前服务计划暂无服务项，请新增服务项'), true)
})

test('设备详情仅保留一个服务管理入口', () => {
  assert.equal(deviceDirectorySource.includes('name="service-management"'), true)
  assert.equal(deviceDirectorySource.includes('name="plans"'), false)
  assert.equal(deviceDirectorySource.includes('name="tasks"'), false)
  assert.equal(deviceDirectorySource.includes('name="records"'), false)
})
