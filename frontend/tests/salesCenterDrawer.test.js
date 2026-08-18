import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync(new URL('../src/views/SalesCenterView.vue', import.meta.url), 'utf8')
const styles = readFileSync(new URL('../src/styles/main.css', import.meta.url), 'utf8')

test('销售负责关系抽屉使用独立滚动容器并展示汇总信息', () => {
  [
    'class="sales-responsibility-drawer"',
    '<el-scrollbar class="sales-responsibility-scroll" always>',
    'const drawerLoading = ref(false)',
    'const responsibilitySummary = computed(',
    '加载销售负责关系失败',
  ].forEach((snippet) => assert.equal(source.includes(snippet), true, snippet))
  assert.equal(source.includes('customer.contracts'), false)
  assert.equal(source.includes('contractCount'), false)
})

test('销售负责关系抽屉具备固定可滚动高度', () => {
  [
    '.sales-responsibility-drawer .el-drawer__body { display: flex; min-height: 0; }',
    '.sales-responsibility-layout { flex: 1; min-height: 0; display: flex; flex-direction: column; }',
    '.sales-responsibility-scroll { flex: 1; min-height: 0; margin-top: 12px; }',
  ].forEach((snippet) => assert.equal(styles.includes(snippet), true, snippet))
})
