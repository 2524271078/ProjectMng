import assert from 'node:assert/strict'
import test from 'node:test'

import { buildPersonPayload } from './personPayload.js'

test('buildPersonPayload omits empty organization when creating', () => {
  const payload = buildPersonPayload({ name: '销售', person_type: 'sales', organization: null }, false)

  assert.equal(Object.hasOwn(payload, 'organization'), false)
})

test('buildPersonPayload sends null organization when editing to clear existing organization', () => {
  const payload = buildPersonPayload({ name: '销售', person_type: 'sales', organization: null }, true)

  assert.equal(payload.organization, null)
})
