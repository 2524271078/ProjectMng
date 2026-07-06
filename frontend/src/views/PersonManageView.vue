<template>
  <div class="page-scroll-layout">
    <div class="section-head">
      <div>
        <span class="eyebrow-dark">People</span>
        <h2>人员管理</h2>
      </div>
      <el-button type="primary" @click="openCreateDialog">新增人员</el-button>
    </div>

    <div class="page-table-scroll">
      <el-table v-loading="peoplePagination.loading" :data="peoplePagination.rows" stripe>
        <el-table-column prop="name" label="姓名" min-width="140" />
        <el-table-column label="人员类型" min-width="130">
          <template #default="scope">{{ personTypeLabel(scope.row.person_type) }}</template>
        </el-table-column>
        <el-table-column prop="position" label="职位" min-width="120" />
        <el-table-column prop="phone" label="电话" min-width="140" />
        <el-table-column prop="email" label="邮箱" min-width="220" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openEditDialog(scope.row)">编辑</el-button>
            <el-button link type="danger" @click="removePerson(scope.row)">删除</el-button>
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
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import OrganizationTreeSelect from '../components/OrganizationTreeSelect.vue'
import { createResource, deleteResource, fetchSalesCustomerRelations, listResource, saveSalesCustomerRelations, updateResource } from '../api/resources'
import { buildPersonPayload } from '../utils/personPayload'
import { applyPaginationResponse, buildPaginationState } from '../utils/pagination'
import { personTypeLabel, personTypeOptions } from '../utils/personTypes'

const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const customerIds = ref([])
const peoplePagination = buildPaginationState()
const form = reactive({ name: '', person_type: 'sales', organization: null, position: '', phone: '', email: '', wechat: '' })

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
