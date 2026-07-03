<template>
  <div class="page-scroll-layout">
    <div class="section-head">
      <div><span class="eyebrow-dark">System</span><h2>系统管理</h2></div>
      <el-button @click="loadAll">刷新</el-button>
    </div>

    <el-tabs model-value="users" class="page-tabs-scroll">
      <el-tab-pane label="用户管理" name="users">
        <el-table :data="users">
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="is_active" label="启用" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="角色管理" name="roles">
        <el-table :data="roles">
          <el-table-column prop="name" label="角色" />
          <el-table-column prop="code" label="编码" />
          <el-table-column prop="status" label="状态" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="菜单权限" name="menus">
        <el-table :data="menus">
          <el-table-column prop="name" label="菜单" />
          <el-table-column prop="code" label="编码" />
          <el-table-column prop="path" label="路径" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="操作日志" name="logs">
        <el-table :data="logs">
          <el-table-column prop="action" label="动作" />
          <el-table-column prop="object_type" label="对象" />
          <el-table-column prop="object_id" label="对象 ID" />
          <el-table-column prop="created_at" label="时间" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { listResource } from '../api/resources'
const users = ref([]); const roles = ref([]); const menus = ref([]); const logs = ref([])
async function loadAll() { users.value = (await listResource('users')).data; roles.value = (await listResource('roles')).data; menus.value = (await listResource('menus')).data; logs.value = (await listResource('audit-logs')).data }
onMounted(loadAll)
</script>
