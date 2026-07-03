<template>
  <div class="split-page">
    <aside class="tree-panel">
      <div class="panel-title">产线 / 产品 / 版本</div>
      <el-button type="primary" plain @click="loadAll">刷新</el-button>
      <el-tree :data="productTree" node-key="key" default-expand-all :props="{ label: 'label', children: 'children' }" @node-click="selectNode" />
    </aside>

    <section class="detail-panel">
      <div class="section-head">
        <div><span class="eyebrow-dark">Product Catalog</span><h2>产品型号管理</h2></div>
        <div class="action-row">
          <el-input v-model="searchKeyword" placeholder="搜索型号 / 编码 / 产品 / 版本" clearable @keyup.enter="handleSearch" />
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
          <el-button @click="openDialog('line')">新增产线</el-button>
          <el-button @click="openDialog('product')">新增产品</el-button>
          <el-button @click="openDialog('version')">新增版本</el-button>
          <el-button type="primary" @click="openDialog('model')">新增型号</el-button>
          <el-button :disabled="!selectedNode" @click="editSelectedNode">编辑当前节点</el-button>
          <el-button :disabled="!selectedNode" type="danger" plain @click="removeSelectedNode">删除当前节点</el-button>
        </div>
      </div>
      <el-alert v-if="!lines.length" title="请先新增产线，再在产线下新增产品、版本和型号。" type="info" show-icon :closable="false" class="mb-16" />
      <div class="page-table-scroll">
        <el-table :data="models" stripe>
        <el-table-column prop="model_name" label="型号名称" min-width="180" />
        <el-table-column prop="model_code" label="型号编码" min-width="160" />
        <el-table-column prop="description" label="说明" min-width="220" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click.stop="editModel(scope.row)">编辑</el-button>
            <el-button link type="danger" @click.stop="removeModel(scope.row)">删除</el-button>
          </template>
        </el-table-column>
        </el-table>
      </div>
    </section>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form :model="form" label-width="100px">
        <template v-if="dialogType === 'line'">
          <el-form-item label="产线名称" required><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="产线编码" required><el-input v-model="form.code" /></el-form-item>
        </template>
        <template v-if="dialogType === 'product'">
          <el-form-item label="所属产线" required><el-select v-model="form.product_line" filterable><el-option v-for="line in lines" :key="line.id" :label="line.name" :value="line.id" /></el-select></el-form-item>
          <el-form-item label="产品名称" required><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="产品编码" required><el-input v-model="form.product_code" /></el-form-item>
        </template>
        <template v-if="dialogType === 'version'">
          <el-form-item label="所属产品" required><el-select v-model="form.product" filterable><el-option v-for="product in products" :key="product.id" :label="product.name" :value="product.id" /></el-select></el-form-item>
          <el-form-item label="版本名称" required><el-input v-model="form.version_name" /></el-form-item>
          <el-form-item label="版本编码" required><el-input v-model="form.version_code" /></el-form-item>
        </template>
        <template v-if="dialogType === 'model'">
          <el-form-item label="所属产品" required><el-select v-model="form.product" filterable @change="form.product_version = null"><el-option v-for="product in products" :key="product.id" :label="product.name" :value="product.id" /></el-select></el-form-item>
          <el-form-item label="产品版本"><el-select v-model="form.product_version" clearable filterable><el-option v-for="version in modelVersionOptions" :key="version.id" :label="version.version_name" :value="version.id" /></el-select></el-form-item>
          <el-form-item label="型号名称" required><el-input v-model="form.model_name" /></el-form-item>
          <el-form-item label="型号编码" required><el-input v-model="form.model_code" /></el-form-item>
        </template>
      </el-form>
      <template #footer><el-button @click="closeDialog">取消</el-button><el-button type="primary" :loading="saving" @click="saveCatalogItem">{{ editingId ? '保存修改' : '保存' }}</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createResource, deleteResource, listResource, updateResource } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'
import { validateCatalogForm } from '../utils/productCatalog'

const lines = ref([])
const products = ref([])
const versions = ref([])
const models = ref([])
const selectedNode = ref(null)
const dialogVisible = ref(false)
const saving = ref(false)
const dialogType = ref('line')
const editingId = ref(null)
const searchKeyword = ref('')
const form = reactive({})
const dialogTitle = computed(() => ({ line: editingId.value ? '编辑产线' : '新增产线', product: editingId.value ? '编辑产品' : '新增产品', version: editingId.value ? '编辑版本' : '新增版本', model: editingId.value ? '编辑型号' : '新增型号' }[dialogType.value]))
const productTree = computed(() => lines.value.map((line) => ({ key: `line-${line.id}`, type: 'line', id: line.id, label: line.name, children: products.value.filter((p) => p.product_line === line.id).map((product) => ({ key: `product-${product.id}`, type: 'product', id: product.id, label: product.name, children: versions.value.filter((v) => v.product === product.id).map((version) => ({ key: `version-${version.id}`, type: 'version', id: version.id, label: version.version_name })) })) })))
const modelVersionOptions = computed(() => versions.value.filter((version) => version.product === form.product))
function currentModelFilters() {
  const params = {}
  if (selectedNode.value?.type === 'line') params.product_line = selectedNode.value.id
  if (selectedNode.value?.type === 'product') params.product = selectedNode.value.id
  if (selectedNode.value?.type === 'version') params.product_version = selectedNode.value.id
  if (searchKeyword.value.trim()) params.search = searchKeyword.value.trim()
  return params
}

async function loadModels() {
  try {
    models.value = unwrapList((await listResource('device-models', currentModelFilters())).data)
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载型号列表失败'))
  }
}

async function loadAll() {
  try {
    lines.value = unwrapList((await listResource('product-lines')).data)
    products.value = unwrapList((await listResource('products')).data)
    versions.value = unwrapList((await listResource('product-versions')).data)
    await loadModels()
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载产品中心数据失败'))
  }
}

function handleSearch() {
  loadModels()
}

function resetSearch() {
  searchKeyword.value = ''
  loadModels()
}

function selectNode(node) {
  selectedNode.value = node
  loadModels()
}

function resetForm() {
  editingId.value = null
  Object.keys(form).forEach((key) => delete form[key])
}

function closeDialog() {
  dialogVisible.value = false
  resetForm()
}

function openDialog(type) {
  if (type === 'product' && !lines.value.length) return ElMessage.warning('请先新增产线')
  if ((type === 'version' || type === 'model') && !products.value.length) return ElMessage.warning('请先新增产品')
  dialogType.value = type
  resetForm()
  if (type === 'product' && selectedNode.value?.type === 'line') form.product_line = selectedNode.value.id
  if (type === 'version' && selectedNode.value?.type === 'product') form.product = selectedNode.value.id
  if (type === 'model') {
    if (selectedNode.value?.type === 'product') form.product = selectedNode.value.id
    if (selectedNode.value?.type === 'version') {
      form.product_version = selectedNode.value.id
      form.product = versions.value.find((version) => version.id === selectedNode.value.id)?.product
    }
  }
  dialogVisible.value = true
}

function dialogResource(type) {
  return { line: 'product-lines', product: 'products', version: 'product-versions', model: 'device-models' }[type]
}

function fillForm(type, row) {
  if (type === 'line') Object.assign(form, { name: row.name || '', code: row.code || '', description: row.description || '' })
  if (type === 'product') Object.assign(form, { product_line: row.product_line || null, name: row.name || '', product_code: row.product_code || '', category: row.category || '', manufacturer: row.manufacturer || null, description: row.description || '' })
  if (type === 'version') Object.assign(form, { product: row.product || null, version_name: row.version_name || '', version_code: row.version_code || '', release_date: row.release_date || null, description: row.description || '' })
  if (type === 'model') Object.assign(form, { product: row.product || null, product_version: row.product_version || null, model_name: row.model_name || '', model_code: row.model_code || '', manufacturer: row.manufacturer || null, description: row.description || '' })
}

function editSelectedNode() {
  if (!selectedNode.value) return
  const type = selectedNode.value.type
  const sourceMap = { line: lines.value, product: products.value, version: versions.value }
  const row = sourceMap[type].find((item) => item.id === selectedNode.value.id)
  if (!row) return ElMessage.warning('当前节点数据不存在，请先刷新')
  dialogType.value = type
  resetForm()
  editingId.value = row.id
  fillForm(type, row)
  dialogVisible.value = true
}

async function removeSelectedNode() {
  if (!selectedNode.value) return
  const typeLabel = { line: '产线', product: '产品', version: '版本' }[selectedNode.value.type]
  const resource = dialogResource(selectedNode.value.type)
  try {
    await ElMessageBox.confirm(`确认删除当前${typeLabel}“${selectedNode.value.label}”？`, '删除确认', { type: 'warning' })
    await deleteResource(resource, selectedNode.value.id)
    ElMessage.success(`${typeLabel}已删除`)
    selectedNode.value = null
    await loadAll()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(formatApiError(error, `删除${typeLabel}失败`))
  }
}

function editModel(row) {
  dialogType.value = 'model'
  resetForm()
  editingId.value = row.id
  fillForm('model', row)
  dialogVisible.value = true
}

async function removeModel(row) {
  try {
    await ElMessageBox.confirm(`确认删除型号“${row.model_name}”？`, '删除确认', { type: 'warning' })
    await deleteResource('device-models', row.id)
    ElMessage.success('型号已删除')
    await loadAll()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(formatApiError(error, '删除型号失败'))
  }
}
async function saveCatalogItem() {
  const message = validateCatalogForm(dialogType.value, form)
  if (message) return ElMessage.warning(message)
  const resource = dialogResource(dialogType.value)
  saving.value = true
  try {
    if (editingId.value) {
      await updateResource(resource, editingId.value, form)
      ElMessage.success('已更新')
    } else {
      await createResource(resource, form)
      ElMessage.success('已保存')
    }
    closeDialog()
    await loadAll()
  } catch (error) {
    ElMessage.error(formatApiError(error, '保存失败'))
  } finally {
    saving.value = false
  }
}
onMounted(loadAll)
</script>
