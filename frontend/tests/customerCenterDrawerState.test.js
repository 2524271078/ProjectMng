import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync(new URL('../src/views/CustomerCenterView.vue', import.meta.url), 'utf8')

test('客户中心项目详情抽屉定义了分页和详情 tab 状态', () => {
  const requiredSnippets = [
    "const projectDetailTab = ref('base')",
    'const projectDeviceDrawerPagination = reactive({ page: 1, pageSize: 5, total: 0 })',
    'const projectContractDrawerPagination = reactive({ page: 1, pageSize: 5, total: 0 })',
    'const projectAttachmentDrawerPagination = reactive({ page: 1, pageSize: 5, total: 0 })',
    'const projectDeviceRows = computed(() => paginateProjectDrawerRows(projectOverview.value?.devices || [], projectDeviceDrawerPagination))',
    'const projectContractRows = computed(() => paginateProjectDrawerRows(projectOverview.value?.contracts || [], projectContractDrawerPagination))',
    'const projectAttachmentRows = computed(() => paginateProjectDrawerRows(projectOverview.value?.attachments || [], projectAttachmentDrawerPagination))',
    "projectDetailTab.value = 'base'",
    'resetProjectDrawerPagination()',
  ]
  requiredSnippets.forEach((snippet) => assert.equal(source.includes(snippet), true, snippet))
})
