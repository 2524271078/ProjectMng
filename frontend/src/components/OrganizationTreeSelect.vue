<template>
  <el-tree-select
    :model-value="modelValue"
    :data="treeData"
    node-key="id"
    :props="treeProps"
    check-strictly
    clearable
    filterable
    :placeholder="placeholder"
    :multiple="multiple"
    collapse-tags
    collapse-tags-tooltip
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listResource } from '../api/resources'
import { buildOrganizationTree } from '../utils/orgTree'

const props = defineProps({
  modelValue: { type: [Number, null], default: null },
  placeholder: { type: String, default: '请选择组织' },
  multiple: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const treeData = ref([])
const treeProps = { label: 'name', children: 'children' }

async function loadOrganizations() {
  const { data } = await listResource('organizations')
  treeData.value = buildOrganizationTree(data.results || data)
}

onMounted(loadOrganizations)
</script>
