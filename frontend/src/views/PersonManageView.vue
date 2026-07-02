<template>
  <div>
    <div class="section-head">
      <div>
        <span class="eyebrow-dark">People</span>
        <h2>人员管理</h2>
      </div>
      <el-button type="primary" @click="openCreateDialog">新增人员</el-button>
    </div>

    <el-table :data="people" stripe>
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="person_type" label="人员类型" />
      <el-table-column prop="position" label="职位" />
      <el-table-column prop="phone" label="电话" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="操作" width="150">
        <template #default="scope">
          <el-button link type="primary" @click="openEditDialog(scope.row)">编辑</el-button>
          <el-button link type="danger" @click="removePerson(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑人员' : '新增人员'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="姓名" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.person_type">
            <el-option label="销售" value="sales" />
            <el-option label="客户联系人" value="customer_contact" />
            <el-option label="内部人员" value="internal" />
            <el-option label="现场运维" value="ops" />
            <el-option label="厂商联系人" value="vendor_contact" />
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

const people = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const customerIds = ref([])
const form = reactive({ name: '', person_type: 'sales', organization: null, position: '', phone: '', email: '', wechat: '' })

async function loadPeople() {
  const { data } = await listResource('people')
  people.value = data.results || data
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
  const payload = { ...form }
  if (!payload.organization) delete payload.organization
  return payload
}

function formatApiError(error) {
  const data = error.response?.data
  if (!data || typeof data === 'string') return data || '保存失败'
  return Object.entries(data).map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join('，') : messages}`).join('；')
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
  await ElMessageBox.confirm(`确认删除人员“${row.name}”？`, '删除确认', { type: 'warning' })
  await deleteResource('people', row.id)
  ElMessage.success('人员已删除')
  await loadPeople()
}

onMounted(loadPeople)
</script>
