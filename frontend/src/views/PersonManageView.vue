<template>
  <div class="page-scroll-layout">
    <div class="section-head">
      <div>
        <span class="eyebrow-dark">People</span>
        <h2>人员管理</h2>
      </div>
      <el-button v-can="['people', 'create']" type="primary" @click="openCreateDialog">新增人员</el-button>
    </div>

    <div class="page-table-scroll">
      <el-table v-loading="peoplePagination.loading" :data="peoplePagination.rows" stripe height="100%">
        <el-table-column prop="name" label="姓名" min-width="140" />
        <el-table-column label="人员类型" min-width="130">
          <template #default="scope">{{ personTypeLabel(scope.row.person_type) }}</template>
        </el-table-column>
        <el-table-column prop="position" label="职位" min-width="120" />
        <el-table-column prop="phone" label="电话" min-width="140" />
        <el-table-column prop="email" label="邮箱" min-width="220" />
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="scope">
            <el-button v-can="['people', 'view']" link type="primary" @click="openDetailDialog(scope.row)">详情</el-button>
            <el-button v-can="['people', 'edit']" link type="primary" @click="openEditDialog(scope.row)">编辑</el-button>
            <el-button v-can="['people', 'delete']" link type="danger" @click="removePerson(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="table-pagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next"
        :current-page="peoplePagination.page"
        :page-size="peoplePagination.pageSize"
        :page-sizes="[10, 20, 50]"
        :total="peoplePagination.total"
        @current-change="handlePageChange"
        @size-change="handlePageSizeChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑人员' : '新增人员'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="姓名" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.person_type">
            <el-option v-for="item in personTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属组织"><OrganizationTreeSelect v-model="form.organization" placeholder="请选择所属公司，可不选" /></el-form-item>
        <el-form-item v-if="form.person_type === 'sales'" label="负责客户">
          <OrganizationTreeSelect v-model="customerIds" multiple placeholder="请选择该销售负责的客户公司" />
        </el-form-item>
        <el-form-item label="职位"><el-input v-model="form.position" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="微信"><el-input v-model="form.wechat" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="savePerson">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" :title="`人员详情 · ${personDetail?.name || ''}`" width="780px" destroy-on-close>
      <div v-loading="detailLoading" class="person-detail">
        <el-descriptions v-if="personDetail" :column="3" border>
          <el-descriptions-item label="人员类型">{{ personTypeLabel(personDetail.person_type) }}</el-descriptions-item>
          <el-descriptions-item label="职位">{{ personDetail.position || '-' }}</el-descriptions-item>
          <el-descriptions-item label="所属组织">{{ personDetail.organization_detail?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ personDetail.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ personDetail.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="微信">{{ personDetail.wechat || '-' }}</el-descriptions-item>
        </el-descriptions>

        <template v-if="personDetail?.person_type === 'sales'">
          <div class="person-detail-section">
            <div class="person-detail-title">负责客户</div>
            <div class="person-detail-summary">
              <el-tag effect="plain">客户 {{ salesCustomers.length }}</el-tag>
              <el-tag effect="plain" type="success">关联设备 {{ relatedDeviceCount }}</el-tag>
              <el-tag effect="plain" type="warning">关联合同 {{ relatedContractCount }}</el-tag>
            </div>
          </div>
          <el-table :data="pagedSalesCustomers" stripe max-height="360">
            <el-table-column prop="name" label="客户公司" min-width="210" />
            <el-table-column prop="region" label="区域" min-width="110">
              <template #default="scope">{{ scope.row.region || '-' }}</template>
            </el-table-column>
            <el-table-column label="设备" min-width="100" align="center">
              <template #default="scope">{{ scope.row.devices?.length || 0 }}</template>
            </el-table-column>
            <el-table-column label="合同" min-width="100" align="center">
              <template #default="scope">{{ scope.row.contracts?.length || 0 }}</template>
            </el-table-column>
          </el-table>
          <div v-if="salesCustomers.length > detailCustomerPageSize" class="detail-customer-pagination">
            <el-pagination
              background
              layout="total, prev, pager, next"
              :current-page="detailCustomerPage"
              :page-size="detailCustomerPageSize"
              :total="salesCustomers.length"
              @current-change="detailCustomerPage = $event"
            />
          </div>
          <el-empty v-if="!detailLoading && !salesCustomers.length" description="暂未分配负责客户" :image-size="72" />
        </template>
        <el-empty v-else-if="!detailLoading" description="该人员不是销售，无负责客户数据" :image-size="72" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import OrganizationTreeSelect from '../components/OrganizationTreeSelect.vue'
import { createResource, deleteResource, fetchSalesCustomerRelations, fetchSalesCustomers, listResource, saveSalesCustomerRelations, updateResource } from '../api/resources'
import { buildPersonPayload } from '../utils/personPayload'
import { applyPaginationResponse, buildPaginationState } from '../utils/pagination'
import { personTypeLabel, personTypeOptions } from '../utils/personTypes'

const dialogVisible = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const saving = ref(false)
const editingId = ref(null)
const customerIds = ref([])
const personDetail = ref(null)
const salesCustomers = ref([])
const detailCustomerPage = ref(1)
const detailCustomerPageSize = 5
const peoplePagination = buildPaginationState()
const form = reactive({ name: '', person_type: 'sales', organization: null, position: '', phone: '', email: '', wechat: '' })

const relatedDeviceCount = computed(() => salesCustomers.value.reduce((total, customer) => total + (customer.devices?.length || 0), 0))
const relatedContractCount = computed(() => salesCustomers.value.reduce((total, customer) => total + (customer.contracts?.length || 0), 0))
const pagedSalesCustomers = computed(() => {
  const start = (detailCustomerPage.value - 1) * detailCustomerPageSize
  return salesCustomers.value.slice(start, start + detailCustomerPageSize)
})

async function loadPeople() {
  peoplePagination.loading = true
  try {
    const { data } = await listResource('people', {
      page: peoplePagination.page,
      page_size: peoplePagination.pageSize,
    })
    applyPaginationResponse(peoplePagination, data)
  } catch (error) {
    ElMessage.error(formatApiError(error))
  } finally {
    peoplePagination.loading = false
  }
}

function handlePageChange(page) {
  peoplePagination.page = page
  loadPeople()
}

function handlePageSizeChange(pageSize) {
  peoplePagination.page = 1
  peoplePagination.pageSize = pageSize
  loadPeople()
}

function resetForm() {
  Object.assign(form, { name: '', person_type: 'sales', organization: null, position: '', phone: '', email: '', wechat: '' })
}

function openCreateDialog() {
  editingId.value = null
  resetForm()
  customerIds.value = []
  dialogVisible.value = true
}

async function openEditDialog(row) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name || '',
    person_type: row.person_type || 'sales',
    organization: row.organization || null,
    position: row.position || '',
    phone: row.phone || '',
    email: row.email || '',
    wechat: row.wechat || '',
  })
  if (row.person_type === 'sales') {
    const { data } = await fetchSalesCustomerRelations(row.id)
    customerIds.value = data.customer_ids || []
  } else {
    customerIds.value = []
  }
  dialogVisible.value = true
}

async function openDetailDialog(row) {
  personDetail.value = row
  salesCustomers.value = []
  detailCustomerPage.value = 1
  detailVisible.value = true
  if (row.person_type !== 'sales') return

  detailLoading.value = true
  try {
    const { data } = await fetchSalesCustomers(row.id)
    salesCustomers.value = Array.isArray(data) ? data : []
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载负责客户失败'))
  } finally {
    detailLoading.value = false
  }
}

function buildPayload() {
  return buildPersonPayload(form, Boolean(editingId.value))
}

function formatApiError(error) {
  const data = error.response?.data
  if (!data || typeof data === 'string') return data || '保存失败'
  return Object.entries(data).map(([field, messages]) => field + ': ' + (Array.isArray(messages) ? messages.join('，') : messages)).join('；')
}

async function savePerson() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写姓名')
    return
  }
  saving.value = true
  try {
    let personId = editingId.value
    if (editingId.value) {
      await updateResource('people', editingId.value, buildPayload())
    } else {
      const { data } = await createResource('people', buildPayload())
      personId = data.id
    }
    if (form.person_type === 'sales') {
      await saveSalesCustomerRelations(personId, customerIds.value)
    }
    ElMessage.success(editingId.value ? '人员已更新' : '人员已新增')
    dialogVisible.value = false
    resetForm()
    editingId.value = null
    customerIds.value = []
    await loadPeople()
  } catch (error) {
    ElMessage.error(formatApiError(error))
  } finally {
    saving.value = false
  }
}

async function removePerson(row) {
  await ElMessageBox.confirm('确认删除人员“' + row.name + '”吗？', '删除确认', { type: 'warning' })
  await deleteResource('people', row.id)
  ElMessage.success('人员已删除')
  await loadPeople()
}

onMounted(loadPeople)
</script>

<style scoped>
.person-detail { min-height: 150px; }
.person-detail-section { display: flex; align-items: center; justify-content: space-between; margin: 22px 0 12px; }
.person-detail-title { color: #1c2b3f; font-size: 16px; font-weight: 700; }
.person-detail-summary { display: flex; gap: 8px; }
.detail-customer-pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
