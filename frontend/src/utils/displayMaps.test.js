import assert from 'node:assert/strict'
import test from 'node:test'

import { projectStageLabel } from './displayMaps.js'

test('projectStageLabel maps internal values to Chinese labels', () => {
  assert.equal(projectStageLabel('new'), '立项')
  assert.equal(projectStageLabel('signed'), '签约')
  assert.equal(projectStageLabel('delivery'), '交付')
  assert.equal(projectStageLabel('ops'), '运维')
})

test('projectStageLabel falls back for unknown values', () => {
  assert.equal(projectStageLabel('custom'), 'custom')
  assert.equal(projectStageLabel(''), '-')
})
