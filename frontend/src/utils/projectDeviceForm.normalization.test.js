import assert from 'node:assert/strict'
import test from 'node:test'

import { parseProductModelTreeValue, toProductModelTreeKey } from './productModelTree.js'
import { buildProjectDevicePayload } from './projectDeviceForm.js'

test('toProductModelTreeKey formats model primary key for tree selection', () => {
  assert.equal(toProductModelTreeKey(12), 'model-12')
  assert.equal(toProductModelTreeKey(null), null)
})

test('parseProductModelTreeValue extracts numeric model primary key from tree selection', () => {
  assert.equal(parseProductModelTreeValue('model-18'), 18)
  assert.equal(parseProductModelTreeValue(25), 25)
  assert.equal(parseProductModelTreeValue('31'), 31)
  assert.equal(parseProductModelTreeValue('product-4'), null)
  assert.equal(parseProductModelTreeValue(null), null)
})

test('buildProjectDevicePayload normalizes tree-select model values before submit', () => {
  const payload = buildProjectDevicePayload(
    {
      device_name: '项目设备',
      serial_number: 'PJ-SN-001',
      device_model: 'model-7',
    },
    {
      customerOrgId: 11,
      salesPersonId: 22,
    },
  )

  assert.equal(payload.device_model, 7)
  assert.equal(payload.customer_org, 11)
  assert.equal(payload.sales_person, 22)
})