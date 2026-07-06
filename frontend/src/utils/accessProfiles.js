export const dataScopeOptions = [
  { label: '全部数据', value: 'all' },
  { label: '本人销售数据', value: 'self' },
  { label: '自定义销售范围', value: 'custom' },
]

const dataScopeLabelMap = Object.fromEntries(dataScopeOptions.map((item) => [item.value, item.label]))

export function dataScopeLabel(value) {
  return dataScopeLabelMap[value] || value || '-'
}