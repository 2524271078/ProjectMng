import test from 'node:test'
import assert from 'node:assert/strict'
import { buildMenuCodeSet, hasActionAccess, hasMenuAccess } from '../src/utils/authz.js'

test('buildMenuCodeSet 提取菜单编码集合', () => {
  const codes = buildMenuCodeSet([{ code: 'customers' }, { code: 'devices' }, { name: '无编码' }])
  assert.equal(codes.has('customers'), true)
  assert.equal(codes.has('devices'), true)
  assert.equal(codes.size, 2)
})

test('hasMenuAccess 在超管和普通用户场景下正确判断', () => {
  const codes = buildMenuCodeSet([{ code: 'customers' }])
  assert.equal(hasMenuAccess({ isSuperuser: true, menuCodes: codes }, 'system'), true)
  assert.equal(hasMenuAccess({ isSuperuser: false, menuCodes: codes }, 'customers'), true)
  assert.equal(hasMenuAccess({ isSuperuser: false, menuCodes: codes }, 'system'), false)
  assert.equal(hasMenuAccess({ isSuperuser: false, menuCodes: codes }, ''), true)
})

test('hasActionAccess 根据菜单动作判断权限', () => {
  const permissions = [['customers', 'view'], ['customers', 'edit'], ['devices', 'view']]
  assert.equal(hasActionAccess({ isSuperuser: false, permissions }, 'customers', 'edit'), true)
  assert.equal(hasActionAccess({ isSuperuser: false, permissions }, 'customers', 'delete'), false)
  assert.equal(hasActionAccess({ isSuperuser: true, permissions: [] }, 'system', 'delete'), true)
  assert.equal(hasActionAccess({ isSuperuser: false, permissions }, '', 'view'), true)
})
