import assert from 'node:assert/strict'
import test from 'node:test'

import { buildProjectDevicePayload, createDefaultProjectDeviceForm } from './projectDeviceForm.js'

test('default project device form creates a new device by default', () => {
  const form = createDefaultProjectDeviceForm()

  assert.equal(form.bind_mode, 'new')
  assert.equal(form.device, null)
  assert.equal(form.device_model, null)
})


test('buildProjectDevicePayload applies current customer and sales ownership', () => {
  const payload = buildProjectDevicePayload(
    {
      device_name: '项目设备',
      serial_number: 'PJ-SN-001',
      device_model: 7,
    },
    {
      customerOrgId: 11,
      salesPersonId: 22,
    },
  )

  assert.equal(payload.customer_org, 11)
  assert.equal(payload.sales_person, 22)
})
