<template>
  <div>
    <div class="section-head">
      <div>
        <span class="eyebrow-dark">People</span>
        <h2>人员管理</h2>
      </div>
      <el-button type="primary" @click="dialogVisible = true">新增人员</el-button>
    </div>

    <el-table :data="people" stripe>
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="person_type" label="人员类型" />
      <el-table-column prop="position" label="职位" />
      <el-table-column prop="phone" label="电话" />
      <el-table-column prop="email" label="邮箱" />
    </el-table>

    <el-dialog v-model="dialogVisible" title="新增人员" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.person_type">
            <el-option label="销售" value="sales" />
            <el-option label="客户联系人" value="customer_contact" />
            <el-option label="内部人员" value="internal" />
            <el-option label="现场运维" value="ops" />
            <el-option label="厂商联系人" value="vendor_contact" />
          </el-select>
        </el-form-item>
        <el-form-item label="组织 ID">
          <el-input-number v-model="form.organization" :min="1" placeholder="可不填" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="form.position" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="createPerson">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createResource, listResource } from '../api/resources'

const people = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  name: '',
  person_type: 'sales',
  organization: null,
  position: '',
  phone: '',
  email: '',
})

async function loadPeople() {
  const { data } = await listResource('people')
  people.value = data.results || data
}

function resetForm() {
  Object.assign(form, { name: '', person_type: 'sales', organization: null, position: '', phone: '', email: '' })
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

async function createPerson() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写姓名')
    return
  }
  saving.value = true
  try {
    await createResource('people', buildPayload())
    ElMessage.success('人员已新增')
    dialogVisible.value = false
    resetForm()
    await loadPeople()
  } catch (error) {
    ElMessage.error(formatApiError(error))
  } finally {
    saving.value = false
  }
}

onMounted(loadPeople)
</script>
