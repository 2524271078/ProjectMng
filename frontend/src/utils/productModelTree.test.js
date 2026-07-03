import assert from 'node:assert/strict'
import test from 'node:test'

import { buildProductModelTree } from './productModelTree.js'

test('buildProductModelTree nests lines products versions and model leaves', () => {
  const tree = buildProductModelTree({
    lines: [{ id: 1, name: '安全产品线' }],
    products: [{ id: 10, name: '边界防护', product_line: 1 }],
    versions: [{ id: 100, version_name: 'V2.0', product: 10 }],
    models: [{ id: 1000, model_name: 'SG-1000', model_code: 'SG1000', product: 10, product_version: 100 }],
  })

  assert.equal(tree[0].label, '安全产品线')
  assert.equal(tree[0].disabled, true)
  assert.equal(tree[0].children[0].label, '边界防护')
  assert.equal(tree[0].children[0].children[0].label, 'V2.0')
  assert.equal(tree[0].children[0].children[0].children[0].label, 'SG-1000')
  assert.equal(tree[0].children[0].children[0].children[0].disabled, false)
  assert.equal(tree[0].children[0].children[0].children[0].type, 'model')
  assert.equal(tree[0].children[0].children[0].children[0].id, 1000)
})

test('buildProductModelTree places models without versions directly under product', () => {
  const tree = buildProductModelTree({
    lines: [{ id: 1, name: '安全产品线' }],
    products: [{ id: 10, name: '边界防护', product_line: 1 }],
    versions: [],
    models: [{ id: 1001, model_name: 'SG-2000', model_code: 'SG2000', product: 10, product_version: null }],
  })

  assert.equal(tree[0].children[0].children[0].label, 'SG-2000')
  assert.equal(tree[0].children[0].children[0].type, 'model')
})

test('buildProductModelTree keeps orphan products and models selectable through root fallback', () => {
  const tree = buildProductModelTree({
    lines: [],
    products: [{ id: 20, name: '孤立产品', product_line: null }],
    versions: [],
    models: [{ id: 2001, model_name: 'ORPHAN-1', model_code: 'ORPHAN1', product: 20, product_version: null }],
  })

  assert.equal(tree[0].label, '孤立产品')
  assert.equal(tree[0].disabled, true)
  assert.equal(tree[0].children[0].label, 'ORPHAN-1')
  assert.equal(tree[0].children[0].disabled, false)
})
