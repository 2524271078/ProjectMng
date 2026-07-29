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

test('客户中心将设备详情、服务和编辑入口分开', () => {
  const requiredSnippets = [
    '@click.stop="openDeviceDetail(scope.row)">详情</el-button>',
    '@click.stop="openDeviceService(scope.row)">服务</el-button>',
    '@click.stop="openDeviceEdit(scope.row)">编辑</el-button>',
    '<el-dialog v-model="deviceServiceVisible" title="设备服务"',
    '<el-dialog v-model="deviceEditVisible" title="编辑设备"',
    '<DeviceDetailDescriptions :device="selectedDevice" />',
  ]
  requiredSnippets.forEach((snippet) => assert.equal(source.includes(snippet), true, snippet))
  assert.equal(source.includes('<el-divider content-position="left">当前服务</el-divider>'), false)
  assert.equal(source.includes('function inspectionTaskStatusLabel(value)'), true)
})
