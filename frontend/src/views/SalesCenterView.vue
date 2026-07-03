<template>
  <div class="page-scroll-layout">
    <div class="section-head">
      <div><span class="eyebrow-dark">Sales Center</span><h2>销售负责关系</h2></div>
      <el-button @click="loadSales">刷新</el-button>
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
import { fetchSalesCustomers, listResource } from '../api/resources'
const sales = ref([]); const customers = ref([]); const drawerVisible = ref(false)
async function loadSales() { const { data } = await listResource('people', { person_type: 'sales' }); sales.value = (data.results || data).filter((p) => p.person_type === 'sales') }
async function openSales(row) { const { data } = await fetchSalesCustomers(row.id); customers.value = data; drawerVisible.value = true }
onMounted(loadSales)
</script>
