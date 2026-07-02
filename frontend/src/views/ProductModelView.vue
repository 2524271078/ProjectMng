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
          <el-button @click="openDialog('line')">新增产线</el-button>
          <el-button @click="openDialog('product')">新增产品</el-button>
          <el-button @click="openDialog('version')">新增版本</el-button>
          <el-button type="primary" @click="openDialog('model')">新增型号</el-button>
        </div>
      </div>
      <el-table :data="filteredModels" stripe>
        <el-table-column prop="model_name" label="型号名称" />
        <el-table-column prop="model_code" label="型号编码" />
        <el-table-column prop="description" label="说明" />
        <el-table-column prop="status" label="状态" />
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form :model="form" label-width="100px">
        <template v-if="dialogType === 'line'">
          <el-form-item label="产线名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="产线编码"><el-input v-model="form.code" /></el-form-item>
        </template>
        <template v-if="dialogType === 'product'">
          <el-form-item label="所属产线"><el-select v-model="form.product_line"><el-option v-for="line in lines" :key="line.id" :label="line.name" :value="line.id" /></el-select></el-form-item>
          <el-form-item label="产品名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="产品编码"><el-input v-model="form.product_code" /></el-form-item>
        </template>
        <template v-if="dialogType === 'version'">
          <el-form-item label="所属产品"><el-select v-model="form.product"><el-option v-for="product in products" :key="product.id" :label="product.name" :value="product.id" /></el-select></el-form-item>
          <el-form-item label="版本名称"><el-input v-model="form.version_name" /></el-form-item>
          <el-form-item label="版本编码"><el-input v-model="form.version_code" /></el-form-item>
        </template>
        <template v-if="dialogType === 'model'">
          <el-form-item label="所属产品"><el-select v-model="form.product"><el-option v-for="product in products" :key="product.id" :label="product.name" :value="product.id" /></el-select></el-form-item>
          <el-form-item label="产品版本"><el-select v-model="form.product_version" clearable><el-option v-for="version in versions" :key="version.id" :label="version.version_name" :value="version.id" /></el-select></el-form-item>
          <el-form-item label="型号名称"><el-input v-model="form.model_name" /></el-form-item>
          <el-form-item label="型号编码"><el-input v-model="form.model_code" /></el-form-item>
        </template>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="saveCatalogItem">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createResource, listResource } from '../api/resources'

const lines = ref([])
const products = ref([])
const versions = ref([])
const models = ref([])
const selectedNode = ref(null)
const dialogVisible = ref(false)
const dialogType = ref('line')
const form = reactive({})
const dialogTitle = computed(() => ({ line: '新增产线', product: '新增产品', version: '新增版本', model: '新增型号' }[dialogType.value]))
const productTree = computed(() => lines.value.map((line) => ({ key: `line-${line.id}`, type: 'line', id: line.id, label: line.name, children: products.value.filter((p) => p.product_line === line.id).map((product) => ({ key: `product-${product.id}`, type: 'product', id: product.id, label: product.name, children: versions.value.filter((v) => v.product === product.id).map((version) => ({ key: `version-${version.id}`, type: 'version', id: version.id, label: version.version_name })) })) })))
const filteredModels = computed(() => {
  if (!selectedNode.value) return models.value
  if (selectedNode.value.type === 'version') return models.value.filter((model) => model.product_version === selectedNode.value.id)
  if (selectedNode.value.type === 'product') return models.value.filter((model) => model.product === selectedNode.value.id)
  if (selectedNode.value.type === 'line') {
    const productIds = products.value.filter((p) => p.product_line === selectedNode.value.id).map((p) => p.id)
    return models.value.filter((model) => productIds.includes(model.product))
  }
  return models.value
})
async function loadAll() { lines.value=(await listResource('product-lines')).data; products.value=(await listResource('products')).data; versions.value=(await listResource('product-versions')).data; models.value=(await listResource('device-models')).data }
function selectNode(node) { selectedNode.value = node }
function openDialog(type) { dialogType.value = type; Object.keys(form).forEach((key) => delete form[key]); if (type === 'product' && selectedNode.value?.type === 'line') form.product_line = selectedNode.value.id; if (type === 'version' && selectedNode.value?.type === 'product') form.product = selectedNode.value.id; if (type === 'model') { if (selectedNode.value?.type === 'product') form.product = selectedNode.value.id; if (selectedNode.value?.type === 'version') { form.product_version = selectedNode.value.id; form.product = versions.value.find((v) => v.id === selectedNode.value.id)?.product } } dialogVisible.value = true }
async function saveCatalogItem() { const resource = { line: 'product-lines', product: 'products', version: 'product-versions', model: 'device-models' }[dialogType.value]; await createResource(resource, form); ElMessage.success('已保存'); dialogVisible.value = false; await loadAll() }
onMounted(loadAll)
</script>
