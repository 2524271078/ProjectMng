<template>
  <div class="page-scroll-layout">
    <div class="section-head">
      <div>
        <span class="eyebrow-dark">System</span>
        <h2>系统管理</h2>
      </div>
      <el-button @click="loadAll">刷新</el-button>
    </div>

    <el-tabs v-model="activeTab" class="page-tabs-scroll">
      <el-tab-pane label="用户管理" name="users">
        <div class="tab-header-actions">
          <div class="tab-tip">支持账号、绑定人员、菜单角色和销售数据范围配置。</div>
          <el-button type="primary" @click="openCreateUserDialog">新增用户</el-button>
        </div>
        <div class="page-table-scroll embedded-table-scroll">
          <el-table v-loading="loading.users" :data="users" stripe>
            <el-table-column prop="username" label="账号" min-width="140" />
            <el-table-column prop="email" label="邮箱" min-width="220" />
            <el-table-column label="启用" width="90">
              <template #default="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="超管" width="90">
              <template #default="scope">
                <el-tag :type="scope.row.is_superuser ? 'danger' : 'info'">{{ scope.row.is_superuser ? '是' : '否' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="绑定人员" min-width="140">
              <template #default="scope">{{ scope.row.access_profile?.bound_person?.name || '-' }}</template>
            </el-table-column>
            <el-table-column label="角色" min-width="220">
              <template #default="scope">
                <div class="tag-list-wrap">
                  <el-tag v-for="role in scope.row.roles || []" :key="role.id" size="small" class="tag-gap">{{ role.name }}</el-tag>
                  <span v-if="!(scope.row.roles || []).length">-</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="数据范围" min-width="160">
              <template #default="scope">{{ resolveDataScopeLabel(scope.row) }}</template>
            </el-table-column>
            <el-table-column label="销售范围" min-width="240" show-overflow-tooltip>
              <template #default="scope">{{ resolveSalesScopeText(scope.row) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click="openEditUserDialog(scope.row)">编辑</el-button>
                <el-button v-if="!scope.row.is_superuser" link type="danger" @click="removeUser(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="角色管理" name="roles">
        <div class="tab-header-actions">
          <div class="tab-tip">角色负责菜单动作授权，用户再叠加个人销售数据范围。</div>
          <el-button type="primary" @click="openCreateRoleDialog">新增角色</el-button>
        </div>
        <div class="page-table-scroll embedded-table-scroll">
          <el-table v-loading="loading.roles" :data="roles" stripe>
            <el-table-column prop="name" label="角色名称" min-width="160" />
            <el-table-column prop="code" label="角色编码" min-width="160" />
            <el-table-column prop="remark" label="说明" min-width="220" show-overflow-tooltip />
            <el-table-column label="权限项" width="100">
              <template #default="scope">{{ permissionCount(scope.row.id) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">{{ scope.row.status === 'active' ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click="openEditRoleDialog(scope.row)">编辑</el-button>
                <el-button link type="danger" @click="removeRole(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="菜单权限" name="menus">
        <div class="page-table-scroll embedded-table-scroll">
          <el-table :data="menus" stripe>
            <el-table-column prop="name" label="菜单名称" min-width="180" />
            <el-table-column prop="code" label="菜单编码" min-width="160" />
            <el-table-column prop="path" label="路由" min-width="180" />
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">{{ scope.row.status === 'active' ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="操作日志" name="logs">
        <div class="page-table-scroll embedded-table-scroll">
          <el-table v-loading="loading.logs" :data="logs" stripe>
            <el-table-column prop="action" label="动作" min-width="120" />
            <el-table-column prop="object_type" label="对象类型" min-width="140" />
            <el-table-column prop="object_id" label="对象 ID" min-width="100" />
            <el-table-column prop="created_at" label="时间" min-width="180" />
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="userDialogVisible" :title="editingUserId ? '编辑用户' : '新增用户'" width="720px">
      <el-form :model="userForm" label-width="110px">
        <div class="dialog-grid two-column-grid">
          <el-form-item label="账号" required>
            <el-input v-model="userForm.username" :disabled="Boolean(editingUserId)" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="userForm.email" />
          </el-form-item>
          <el-form-item :label="editingUserId ? '重置密码' : '密码'" :required="!editingUserId">
            <el-input v-model="userForm.password" type="password" show-password placeholder="编辑时留空表示不修改" />
          </el-form-item>
          <el-form-item label="绑定人员">
            <el-select v-model="userForm.bound_person_id" clearable filterable placeholder="可选，绑定人员档案">
              <el-option v-for="person in people" :key="person.id" :label="person.name + '（' + personTypeLabel(person.person_type) + '）'" :value="person.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="账号状态">
            <el-switch v-model="userForm.is_active" inline-prompt active-text="启用" inactive-text="停用" />
          </el-form-item>
          <el-form-item label="超级管理员">
            <el-switch v-model="userForm.is_superuser" inline-prompt active-text="是" inactive-text="否" />
          </el-form-item>
        </div>

        <el-form-item label="角色权限">
          <el-select v-model="userForm.role_ids" multiple collapse-tags collapse-tags-tooltip filterable placeholder="请选择角色">
            <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="数据范围">
          <el-segmented v-model="userForm.data_scope_type" :options="dataScopeSegmentOptions" :disabled="userForm.is_superuser" />
        </el-form-item>

        <el-alert v-if="showSelfScopeHint" type="warning" :closable="false" show-icon title="本人销售数据要求绑定一个销售类型的人员档案。" />

        <el-form-item v-if="!userForm.is_superuser && userForm.data_scope_type === 'custom'" label="销售范围" required>
          <el-select v-model="userForm.sales_scope_ids" multiple collapse-tags collapse-tags-tooltip filterable placeholder="请选择允许查看的销售数据">
            <el-option v-for="sales in salesPeople" :key="sales.id" :label="sales.name" :value="sales.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving.user" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="roleDialogVisible" :title="editingRoleId ? '编辑角色' : '新增角色'" width="840px">
      <el-form :model="roleForm" label-width="100px">
        <div class="dialog-grid two-column-grid">
          <el-form-item label="角色名称" required>
            <el-input v-model="roleForm.name" />
          </el-form-item>
          <el-form-item label="角色编码" required>
            <el-input v-model="roleForm.code" :disabled="Boolean(editingRoleId)" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="roleForm.status">
              <el-option label="启用" value="active" />
              <el-option label="停用" value="inactive" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="说明">
          <el-input v-model="roleForm.remark" type="textarea" :rows="2" />
        </el-form-item>

        <div class="permission-panel">
          <div class="permission-panel-head">
            <strong>菜单动作授权</strong>
            <span>勾选后表示该角色允许执行对应动作。</span>
          </div>
          <div class="permission-grid">
            <div v-for="menu in permissionMenus" :key="menu.id" class="permission-row">
              <div class="permission-menu-meta">
                <strong>{{ menu.name }}</strong>
                <span>{{ menu.code }}</span>
              </div>
              <el-checkbox-group v-model="rolePermissionMap[String(menu.id)]">
                <el-checkbox v-for="action in actionOptions" :key="action.value" :label="action.value">{{ action.label }}</el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving.role" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createResource, deleteResource, listAllResource, listResource, updateResource } from '../api/resources'
import { dataScopeLabel, dataScopeOptions } from '../utils/accessProfiles'
import { personTypeLabel } from '../utils/personTypes'
import { buildPermissionRecordsDiff, groupPermissionPairsByMenu } from '../utils/permissionMatrix'

const activeTab = ref('users')
const userDialogVisible = ref(false)
const roleDialogVisible = ref(false)
const editingUserId = ref(null)
const editingRoleId = ref(null)
const users = ref([])
const roles = ref([])
const menus = ref([])
const permissions = ref([])
const people = ref([])
const logs = ref([])

const loading = reactive({ users: false, roles: false, logs: false })
const saving = reactive({ user: false, role: false })

const userForm = reactive({
  username: '',
  email: '',
  password: '',
  is_active: true,
  is_superuser: false,
  role_ids: [],
  bound_person_id: null,
  data_scope_type: 'custom',
  sales_scope_ids: [],
})

const roleForm = reactive({
  name: '',
  code: '',
  remark: '',
  status: 'active',
})

const rolePermissionMap = reactive({})
const actionOptions = [
  { label: '查看', value: 'view' },
  { label: '新增', value: 'create' },
  { label: '编辑', value: 'edit' },
  { label: '删除', value: 'delete' },
]
const dataScopeSegmentOptions = dataScopeOptions.map((item) => ({ label: item.label, value: item.value }))

const salesPeople = computed(() => people.value.filter((item) => item.person_type === 'sales'))
const permissionMenus = computed(() => menus.value.filter((item) => item.code))
const boundPerson = computed(() => people.value.find((item) => item.id === userForm.bound_person_id) || null)
const showSelfScopeHint = computed(() => !userForm.is_superuser && userForm.data_scope_type === 'self' && boundPerson.value?.person_type !== 'sales')

function resetUserForm() {
  Object.assign(userForm, {
    username: '',
    email: '',
    password: '',
    is_active: true,
    is_superuser: false,
    role_ids: [],
    bound_person_id: null,
    data_scope_type: 'custom',
    sales_scope_ids: [],
  })
}

function resetRoleForm() {
  Object.assign(roleForm, {
    name: '',
    code: '',
    remark: '',
    status: 'active',
  })
  resetRolePermissionMap()
}

function resetRolePermissionMap(selected = {}) {
  Object.keys(rolePermissionMap).forEach((key) => {
    delete rolePermissionMap[key]
  })
  permissionMenus.value.forEach((menu) => {
    rolePermissionMap[String(menu.id)] = [...(selected[String(menu.id)] || [])]
  })
}

function normalizeListData(data) {
  return Array.isArray(data) ? data : data.results || []
}

function permissionCount(roleId) {
  return permissions.value.filter((item) => item.role === roleId).length
}

function resolveDataScopeLabel(row) {
  if (row.is_superuser) return '全部数据（超管）'
  return dataScopeLabel(row.access_profile?.data_scope_type)
}

function resolveSalesScopeText(row) {
  if (row.is_superuser) return '全部销售数据'
  const profile = row.access_profile
  if (!profile) return '-'
  if (profile.data_scope_type === 'all') return '全部销售数据'
  if (profile.data_scope_type === 'self') return profile.bound_person?.name || '需绑定销售人员'
  const salesScope = profile.sales_scope || []
  return salesScope.length ? salesScope.map((item) => item.name).join('、') : '-'
}

function buildUserPayload() {
  const payload = {
    username: userForm.username.trim(),
    email: userForm.email.trim(),
    is_active: userForm.is_active,
    is_staff: userForm.is_superuser,
    is_superuser: userForm.is_superuser,
    role_ids: userForm.is_superuser ? [] : [...userForm.role_ids],
    bound_person_id: userForm.bound_person_id || null,
    data_scope_type: userForm.is_superuser ? 'all' : userForm.data_scope_type,
    sales_scope_ids: userForm.is_superuser ? [] : [...userForm.sales_scope_ids],
  }
  if (userForm.password.trim()) payload.password = userForm.password.trim()
  return payload
}

function buildRolePayload() {
  return {
    name: roleForm.name.trim(),
    code: roleForm.code.trim(),
    remark: roleForm.remark.trim(),
    status: roleForm.status,
  }
}

function formatApiError(error, fallback = '保存失败') {
  const data = error.response?.data
  if (!data) return fallback
  if (typeof data === 'string') return data
  return Object.entries(data)
    .map(([field, messages]) => field + ': ' + (Array.isArray(messages) ? messages.join('，') : messages))
    .join('；')
}

async function loadAll() {
  loading.users = true
  loading.roles = true
  loading.logs = true
  try {
    const [usersResponse, rolesResponse, menusResponse, permissionsResponse, peopleResponse, logsResponse] = await Promise.all([
      listResource('users'),
      listResource('roles'),
      listResource('menus'),
      listResource('permissions'),
      listAllResource('people', { page_size: 100 }),
      listResource('audit-logs'),
    ])
    users.value = normalizeListData(usersResponse.data)
    roles.value = normalizeListData(rolesResponse.data)
    menus.value = normalizeListData(menusResponse.data)
    permissions.value = normalizeListData(permissionsResponse.data)
    people.value = normalizeListData(peopleResponse.data)
    logs.value = normalizeListData(logsResponse.data)
    resetRolePermissionMap()
  } catch (error) {
    ElMessage.error(formatApiError(error, '系统管理数据加载失败'))
  } finally {
    loading.users = false
    loading.roles = false
    loading.logs = false
  }
}

function openCreateUserDialog() {
  editingUserId.value = null
  resetUserForm()
  userDialogVisible.value = true
}

function openEditUserDialog(row) {
  editingUserId.value = row.id
  Object.assign(userForm, {
    username: row.username || '',
    email: row.email || '',
    password: '',
    is_active: Boolean(row.is_active),
    is_superuser: Boolean(row.is_superuser),
    role_ids: (row.roles || []).map((item) => item.id),
    bound_person_id: row.access_profile?.bound_person?.id || null,
    data_scope_type: row.access_profile?.data_scope_type || (row.is_superuser ? 'all' : 'custom'),
    sales_scope_ids: (row.access_profile?.sales_scope || []).map((item) => item.id),
  })
  userDialogVisible.value = true
}

async function saveUser() {
  if (!userForm.username.trim()) {
    ElMessage.warning('请填写账号')
    return
  }
  if (!editingUserId.value && !userForm.password.trim()) {
    ElMessage.warning('请填写密码')
    return
  }
  if (!userForm.is_superuser && userForm.data_scope_type === 'custom' && !userForm.sales_scope_ids.length) {
    ElMessage.warning('请选择销售范围')
    return
  }
  if (!userForm.is_superuser && userForm.data_scope_type === 'self' && boundPerson.value?.person_type !== 'sales') {
    ElMessage.warning('本人销售数据需绑定销售类型人员')
    return
  }

  saving.user = true
  try {
    if (editingUserId.value) {
      await updateResource('users', editingUserId.value, buildUserPayload())
    } else {
      await createResource('users', buildUserPayload())
    }
    ElMessage.success(editingUserId.value ? '用户已更新' : '用户已新增')
    userDialogVisible.value = false
    resetUserForm()
    editingUserId.value = null
    await loadAll()
  } catch (error) {
    ElMessage.error(formatApiError(error))
  } finally {
    saving.user = false
  }
}

async function removeUser(row) {
  await ElMessageBox.confirm('确认删除用户“' + row.username + '”吗？', '删除确认', { type: 'warning' })
  await deleteResource('users', row.id)
  ElMessage.success('用户已删除')
  await loadAll()
}

function openCreateRoleDialog() {
  editingRoleId.value = null
  resetRoleForm()
  roleDialogVisible.value = true
}

function openEditRoleDialog(row) {
  editingRoleId.value = row.id
  Object.assign(roleForm, {
    name: row.name || '',
    code: row.code || '',
    remark: row.remark || '',
    status: row.status || 'active',
  })
  resetRolePermissionMap(groupPermissionPairsByMenu(row.permission_pairs || []))
  roleDialogVisible.value = true
}

async function syncRolePermissions(roleId) {
  const existingRecords = permissions.value
    .filter((item) => item.role === roleId)
    .map((item) => ({ id: item.id, menu: item.menu, action: item.action }))
  const diff = buildPermissionRecordsDiff(existingRecords, rolePermissionMap)
  await Promise.all(diff.toDeleteIds.map((id) => deleteResource('permissions', id)))
  await Promise.all(diff.toCreate.map((item) => createResource('permissions', { role: roleId, menu: item.menu, action: item.action })))
}

async function saveRole() {
  if (!roleForm.name.trim() || !roleForm.code.trim()) {
    ElMessage.warning('请填写角色名称和编码')
    return
  }

  saving.role = true
  try {
    let roleId = editingRoleId.value
    if (editingRoleId.value) {
      await updateResource('roles', editingRoleId.value, buildRolePayload())
    } else {
      const { data } = await createResource('roles', buildRolePayload())
      roleId = data.id
    }
    await syncRolePermissions(roleId)
    ElMessage.success(editingRoleId.value ? '角色已更新' : '角色已新增')
    roleDialogVisible.value = false
    resetRoleForm()
    editingRoleId.value = null
    await loadAll()
  } catch (error) {
    ElMessage.error(formatApiError(error))
  } finally {
    saving.role = false
  }
}

async function removeRole(row) {
  await ElMessageBox.confirm('确认删除角色“' + row.name + '”吗？该角色上的授权会一并失效。', '删除确认', { type: 'warning' })
  await deleteResource('roles', row.id)
  ElMessage.success('角色已删除')
  await loadAll()
}

onMounted(loadAll)
</script>

<style scoped>
.tab-header-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.tab-tip {
  color: #617284;
  font-size: 13px;
}

.embedded-table-scroll {
  min-height: 0;
}

.dialog-grid {
  display: grid;
  gap: 0 16px;
}

.two-column-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.permission-panel {
  border: 1px solid #e5edf3;
  border-radius: 12px;
  padding: 14px 16px;
  background: #f8fbfd;
}

.permission-panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  color: #617284;
  font-size: 13px;
}

.permission-grid {
  display: grid;
  gap: 12px;
  max-height: 420px;
  overflow: auto;
}

.permission-row {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e7eef4;
}

.permission-menu-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.permission-menu-meta strong {
  font-size: 14px;
  color: #1f2937;
}

.permission-menu-meta span {
  font-size: 12px;
  color: #7b8b9a;
}

.tag-list-wrap {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

@media (max-width: 900px) {
  .two-column-grid {
    grid-template-columns: 1fr;
  }

  .permission-row {
    grid-template-columns: 1fr;
  }

  .permission-panel-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
