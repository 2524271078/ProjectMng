<template>
  <el-tree-select
    :model-value="treeValue"
    :data="treeData"
    node-key="key"
    :props="treeProps"
    check-strictly
    clearable
    filterable
    :placeholder="placeholder"
    @update:model-value="handleUpdate"
  />
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listAllResource } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'
import { buildProductModelTree, parseProductModelTreeValue, toProductModelTreeKey } from '../utils/productModelTree'

const props = defineProps({
  modelValue: { type: [Number, null], default: null },
  placeholder: { type: String, default: '请选择具体型号' },
})

const emit = defineEmits(['update:modelValue'])

const treeData = ref([])
const treeProps = { label: 'label', children: 'children', disabled: 'disabled' }
const treeValue = computed(() => toProductModelTreeKey(props.modelValue))

function handleUpdate(value) {
  emit('update:modelValue', parseProductModelTreeValue(value))
}

async function loadProductCatalogTree() {
  try {
    const [linesResult, productsResult, versionsResult, modelsResult] = await Promise.all([
      listAllResource('product-lines'),
      listAllResource('products'),
      listAllResource('product-versions'),
      listAllResource('device-models'),
    ])
    treeData.value = buildProductModelTree({
      lines: unwrapList(linesResult.data),
      products: unwrapList(productsResult.data),
      versions: unwrapList(versionsResult.data),
      models: unwrapList(modelsResult.data),
    })
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载产品型号目录失败'))
  }
}

onMounted(loadProductCatalogTree)
</script>