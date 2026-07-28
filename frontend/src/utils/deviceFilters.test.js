import assert from 'node:assert/strict'
import test from 'node:test'

import { filterDevices } from './deviceFilters.js'

const sampleDevices = [
  { id: 1, current_service_status: '保内', service_type: 'new_install', current_signing_subject: 'direct' },
  { id: 2, current_service_status: '保外', service_type: 'renewal', current_signing_subject: 'agent' },
  { id: 3, current_service_status: '保外', service_type: 'offline', current_signing_subject: 'direct' },
]

test('filterDevices keeps all devices when no filters are applied', () => {
  assert.deepEqual(filterDevices(sampleDevices, { warrantyStatus: 'all', serviceType: 'all' }).map((item) => item.id), [1, 2, 3])
})

test('filterDevices filters by warranty status', () => {
  assert.deepEqual(filterDevices(sampleDevices, { warrantyStatus: 'in', serviceType: 'all' }).map((item) => item.id), [1])
  assert.deepEqual(filterDevices(sampleDevices, { warrantyStatus: 'out', serviceType: 'all' }).map((item) => item.id), [2, 3])
})

test('filterDevices filters by device service type', () => {
  assert.deepEqual(filterDevices(sampleDevices, { warrantyStatus: 'all', serviceType: 'renewal' }).map((item) => item.id), [2])
  assert.deepEqual(filterDevices(sampleDevices, { warrantyStatus: 'all', serviceType: 'offline' }).map((item) => item.id), [3])
})

test('filterDevices combines warranty and device service type filters', () => {
  assert.deepEqual(filterDevices(sampleDevices, { warrantyStatus: 'out', serviceType: 'offline' }).map((item) => item.id), [3])
})

test('filterDevices filters by current signing subject', () => {
  assert.deepEqual(filterDevices(sampleDevices, { signingSubject: 'agent' }).map((item) => item.id), [2])
  assert.deepEqual(filterDevices(sampleDevices, { warrantyStatus: 'out', signingSubject: 'direct' }).map((item) => item.id), [3])
})
