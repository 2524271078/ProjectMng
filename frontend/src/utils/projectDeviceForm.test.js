import assert from 'node:assert/strict'
import test from 'node:test'

import { buildProjectDeviceBindingPayload, buildProjectDevicePayload, createDefaultProjectDeviceForm } from './projectDeviceForm.js'

test('default project device form creates a new device by default', () => {
  const form = createDefaultProjectDeviceForm()

  assert.equal(form.bind_mode, 'new')
  assert.equal(form.device, null)
  assert.equal(form.device_model, null)
  assert.equal(form.service_type, 'new_install')
  assert.equal(form.service_start_date, '')
  assert.equal(form.service_end_date, '')
  assert.equal(form.offline_date, '')
})

test('buildProjectDevicePayload applies current customer and sales ownership', () => {
  const payload = buildProjectDevicePayload(
    {
      device_name: 'Project Device',
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

test('buildProjectDevicePayload keeps optional nonstandard name for nonstandard devices', () => {
  const payload = buildProjectDevicePayload(
    {
      device_name: 'Custom Device',
      serial_number: 'NONSTANDARD-SN-001',
      device_model: 7,
      is_standard_product: false,
      nonstandard_name: 'Customer Specific Variant',
    },
    {
      customerOrgId: 11,
      salesPersonId: 22,
    },
  )

  assert.equal(payload.nonstandard_name, 'Customer Specific Variant')
})

test('buildProjectDeviceBindingPayload keeps service cycle fields', () => {
  const payload = buildProjectDeviceBindingPayload({
    deploy_location: 'Main Room',
    device_project_type: 'Formal Device',
    service_type: 'renewal',
    service_start_date: '2026-07-01',
    service_end_date: '2027-06-30',
  })

  assert.equal(payload.quantity, 1)
  assert.equal(payload.deploy_location, 'Main Room')
  assert.equal(payload.device_project_type, 'Formal Device')
  assert.equal(payload.service_type, 'renewal')
  assert.equal(payload.service_start_date, '2026-07-01')
  assert.equal(payload.service_end_date, '2027-06-30')
})

test('buildProjectDeviceBindingPayload keeps offline date for offline devices', () => {
  const payload = buildProjectDeviceBindingPayload({
    deploy_location: 'Main Room',
    device_project_type: 'Formal Device',
    service_type: 'offline',
    service_start_date: '2026-07-01',
    service_end_date: '2027-06-30',
    offline_date: '2026-12-31',
  })

  assert.equal(payload.service_type, 'offline')
  assert.equal(payload.offline_date, '2026-12-31')
})
