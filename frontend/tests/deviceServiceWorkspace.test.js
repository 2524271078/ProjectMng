import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync(new URL('../src/components/DeviceServiceWorkspace.vue', import.meta.url), 'utf8')
const deviceDirectorySource = readFileSync(new URL('../src/views/DeviceDirectoryView.vue', import.meta.url), 'utf8')

test('设备服务页仅展示具体服务项，不展示服务计划总览表', () => {
  assert.equal(source.includes(':data="plans"'), false)
  assert.equal(source.includes(':data="paginatedSchedules"'), true)
  assert.equal(source.includes('当前服务计划暂无服务项，请新增服务项'), true)
})

test('设备服务的服务项、任务和运维记录均采用分页展示', () => {
  assert.equal(source.includes(':data="paginatedSchedules"'), true)
  assert.equal(source.includes(':data="paginatedTasks"'), true)
  assert.equal(source.includes(':data="paginatedRecords"'), true)
  assert.equal(source.includes('const servicePageSize = 10'), true)
  assert.equal(source.includes('schedulePage.value = 1'), true)
  assert.equal(source.includes('taskPage.value = 1'), true)
  assert.equal(source.includes('recordPage.value = 1'), true)
})

test('设备详情仅保留一个服务管理入口', () => {
  assert.equal(deviceDirectorySource.includes('name="service-management"'), true)
  assert.equal(deviceDirectorySource.includes('name="plans"'), false)
  assert.equal(deviceDirectorySource.includes('name="tasks"'), false)
  assert.equal(deviceDirectorySource.includes('name="records"'), false)
})
