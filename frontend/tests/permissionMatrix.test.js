import test from 'node:test'
import assert from 'node:assert/strict'
import { buildPermissionRecordsDiff, groupPermissionPairsByMenu } from '../src/utils/permissionMatrix.js'

test('groupPermissionPairsByMenu 按菜单聚合动作', () => {
  const grouped = groupPermissionPairsByMenu([[1, 'view'], [1, 'edit'], [2, 'view']])
  assert.deepEqual(grouped, { '1': ['edit', 'view'], '2': ['view'] })
})

test('buildPermissionRecordsDiff 生成新增和删除列表', () => {
  const existing = [
    { id: 11, menu: 1, action: 'view' },
    { id: 12, menu: 1, action: 'edit' },
    { id: 13, menu: 2, action: 'view' },
  ]
  const selected = { '1': ['view', 'delete'], '3': ['view'] }
  const diff = buildPermissionRecordsDiff(existing, selected)
  assert.deepEqual(diff.toCreate, [
    { menu: 1, action: 'delete' },
    { menu: 3, action: 'view' },
  ])
  assert.deepEqual(diff.toDeleteIds, [12, 13])
})
