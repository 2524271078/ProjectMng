import test from 'node:test'
import assert from 'node:assert/strict'
import { formatLocalDateTime } from './localDateTime.js'

test('formatLocalDateTime keeps local date and time without converting to UTC', () => {
  const localDate = new Date(2026, 6, 29, 14, 5, 6)

  assert.equal(formatLocalDateTime(localDate), '2026-07-29T14:05:06')
})
