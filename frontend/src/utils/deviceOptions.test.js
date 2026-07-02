import assert from 'node:assert/strict'
import test from 'node:test'

import { formatDeviceOptionLabel } from './deviceOptions.js'

test('formatDeviceOptionLabel includes device model name when available', () => {
  const label = formatDeviceOptionLabel(
    { name: '防火墙', serial_number: 'SN001', device_model: 2 },
    [{ id: 2, model_name: 'SG-3000', model_code: 'SG3000' }],
  )

  assert.equal(label, '防火墙 / SN001 / SG-3000')
})

test('formatDeviceOptionLabel works without matched model', () => {
  const label = formatDeviceOptionLabel({ name: '防火墙', serial_number: 'SN001', device_model: 99 }, [])

  assert.equal(label, '防火墙 / SN001')
})
