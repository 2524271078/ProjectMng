import assert from 'node:assert/strict'
import test from 'node:test'

import { buildOrganizationTree } from './orgTree.js'

test('buildOrganizationTree groups flat organizations by parent id', () => {
  const tree = buildOrganizationTree([
    { id: 3, name: '国网宁河供电公司', parent: 2 },
    { id: 1, name: '国家电网有限公司', parent: null },
    { id: 2, name: '国网天津市电力公司', parent: 1 },
    { id: 4, name: '独立客户', parent: null },
  ])

  assert.deepEqual(tree.map((item) => item.name), ['国家电网有限公司', '独立客户'])
  assert.equal(tree[0].children[0].name, '国网天津市电力公司')
  assert.equal(tree[0].children[0].children[0].name, '国网宁河供电公司')
})

test('buildOrganizationTree keeps orphan organizations at root', () => {
  const tree = buildOrganizationTree([{ id: 9, name: '孤立组织', parent: 99 }])

  assert.equal(tree[0].name, '孤立组织')
  assert.deepEqual(tree[0].children, [])
})
