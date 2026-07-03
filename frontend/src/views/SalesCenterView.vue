<template>
  <div class="page-scroll-layout">
    <div class="section-head">
      <div><span class="eyebrow-dark">Sales Center</span><h2>销售负责关系</h2></div>
      <div class="action-row">
        <el-input v-model="searchKeyword" placeholder="搜索销售姓名 / 电话 / 邮箱" clearable @keyup.enter="handleSearch" />
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
        <el-button @click="loadSales">刷新</el-button>
      </div>
    </div>

    <div class="page-table-scroll">
      <el-table :data="sales" @row-click="openSales">
        <el-table-column prop="name" label="销售" />
        <el-table-column prop="phone" label="电话" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="status" label="状态" />
      </el-table>
    </div>

    <el-drawer v-model="drawerVisible" size="56%" title="负责客户、设备和合同">
      <div class="page-table-scroll">
        <el-table :data="customers">
          <el-table-column prop="name" label="客户" />
          <el-table-column label="设备">
            <template #default="scope"><el-tag v-for="d in scope.row.devices" :key="d.id" class="tag-gap">{{ d.name }}</el-tag></template>
          </el-table-column>
          <el-table-column label="合同">
            <template #default="scope"><el-tag v-for="c in scope.row.contracts" :key="c.id" type="success" class="tag-gap">{{ c.contract_no }}</el-tag></template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchSalesCustomers, listResource } from '../api/resources'
import { formatApiError } from '../utils/apiData'
const sales = ref([]); const customers = ref([]); const drawerVisible = ref(false); const searchKeyword = ref('')
async function loadSales() { try { const params = { person_type: 'sales' }; if (searchKeyword.value.trim()) params.search = searchKeyword.value.trim(); const { data } = await listResource('people', params); sales.value = (data.results || data).filter((p) => p.person_type === 'sales') } catch (error) { ElMessage.error(formatApiError(error, '加载销售列表失败')) } }
function handleSearch() { loadSales() }
function resetSearch() { searchKeyword.value = ''; loadSales() }
async function openSales(row) { const { data } = await fetchSalesCustomers(row.id); customers.value = data; drawerVisible.value = true }
onMounted(loadSales)
</script>
