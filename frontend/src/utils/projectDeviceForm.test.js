import assert from 'node:assert/strict'
import test from 'node:test'

import { createDefaultProjectDeviceForm } from './projectDeviceForm.js'

test('default project device form creates a new device by default', () => {
  const form = createDefaultProjectDeviceForm()

  assert.equal(form.bind_mode, 'new')
  assert.equal(form.device, null)
  assert.equal(form.device_model, null)
})
