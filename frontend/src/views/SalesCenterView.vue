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
      <el-table v-loading="salesPagination.loading" :data="salesPagination.rows" height="100%" @row-click="openSales">
        <el-table-column prop="name" label="销售" />
        <el-table-column prop="phone" label="电话" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="status" label="状态" />
      </el-table>
    </div>
    <div class="table-pagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next"
        :current-page="salesPagination.page"
        :page-size="salesPagination.pageSize"
        :page-sizes="[10, 20, 50]"
        :total="salesPagination.total"
        @current-change="handlePageChange"
        @size-change="handlePageSizeChange"
      />
    </div>

    <el-drawer v-model="drawerVisible" class="sales-responsibility-drawer" size="56%" :title="`${selectedSalesName || '销售'}负责的客户和设备`">
      <div v-loading="drawerLoading" class="sales-responsibility-layout">
        <div class="sales-responsibility-summary">
          <span>共 {{ responsibilitySummary.customerCount }} 个客户</span>
          <span>{{ responsibilitySummary.deviceCount }} 台设备</span>
        </div>

        <el-scrollbar class="sales-responsibility-scroll" always>
          <div v-if="customers.length" class="sales-responsibility-list">
            <article v-for="customer in customers" :key="customer.id" class="sales-responsibility-card">
              <header class="sales-responsibility-card__header">
                <div>
                  <span class="sales-responsibility-card__label">客户</span>
                  <strong>{{ customer.name }}</strong>
                </div>
                <div class="sales-responsibility-card__counts">
                  <span>设备 {{ customer.devices?.length || 0 }}</span>
                </div>
              </header>

              <section class="sales-responsibility-group">
                <h3>设备</h3>
                <div v-if="customer.devices?.length" class="sales-responsibility-tags">
                  <el-tag v-for="device in customer.devices" :key="device.id" effect="plain">
                    {{ device.name || device.serial_number }}
                  </el-tag>
                </div>
                <span v-else class="sales-responsibility-empty">暂无设备</span>
              </section>
            </article>
          </div>
          <el-empty v-else-if="!drawerLoading" description="该销售暂未负责客户" />
        </el-scrollbar>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchSalesCustomers, listResource } from '../api/resources'
import { formatApiError } from '../utils/apiData'
import { applyPaginationResponse, buildPaginationState } from '../utils/pagination'

const customers = ref([])
const drawerVisible = ref(false)
const drawerLoading = ref(false)
const selectedSalesName = ref('')
const searchKeyword = ref('')
const salesPagination = buildPaginationState()

const responsibilitySummary = computed(() => customers.value.reduce((summary, customer) => ({
  customerCount: summary.customerCount + 1,
  deviceCount: summary.deviceCount + (customer.devices?.length || 0),
}), { customerCount: 0, deviceCount: 0 }))

async function loadSales() {
  salesPagination.loading = true
  try {
    const params = {
      person_type: 'sales',
      page: salesPagination.page,
      page_size: salesPagination.pageSize,
    }
    if (searchKeyword.value.trim()) params.search = searchKeyword.value.trim()

    const { data } = await listResource('people', params)
    applyPaginationResponse(salesPagination, data)
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载销售列表失败'))
  } finally {
    salesPagination.loading = false
  }
}

function handleSearch() {
  salesPagination.page = 1
  loadSales()
}

function resetSearch() {
  searchKeyword.value = ''
  salesPagination.page = 1
  loadSales()
}

function handlePageChange(page) {
  salesPagination.page = page
  loadSales()
}

function handlePageSizeChange(pageSize) {
  salesPagination.page = 1
  salesPagination.pageSize = pageSize
  loadSales()
}

async function openSales(row) {
  selectedSalesName.value = row.name
  drawerVisible.value = true
  drawerLoading.value = true
  customers.value = []
  try {
    const { data } = await fetchSalesCustomers(row.id)
    customers.value = data
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载销售负责关系失败'))
  } finally {
    drawerLoading.value = false
  }
}

onMounted(loadSales)
</script>
