import assert from 'node:assert/strict'
import test from 'node:test'

import { validateCatalogForm } from './productCatalog.js'

test('validateCatalogForm requires line code and name', () => {
  assert.equal(validateCatalogForm('line', { name: '', code: '' }), '请填写产线名称和产线编码')
})

test('validateCatalogForm requires product line before product', () => {
  assert.equal(validateCatalogForm('product', { name: '防火墙', product_code: 'FW' }), '请先选择所属产线')
})

test('validateCatalogForm requires product before version', () => {
  assert.equal(validateCatalogForm('version', { version_name: 'V1', version_code: '1.0' }), '请先选择所属产品')
})

test('validateCatalogForm requires product and model fields before model', () => {
  assert.equal(validateCatalogForm('model', { product: 1, model_name: '', model_code: '' }), '请填写型号名称和型号编码')
})

test('validateCatalogForm returns empty string for valid model', () => {
  assert.equal(validateCatalogForm('model', { product: 1, model_name: 'SG-1000', model_code: 'SG1000' }), '')
})
