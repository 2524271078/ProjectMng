export const personTypeOptions = [
  { label: '销售', value: 'sales' },
  { label: '客户联系人', value: 'customer_contact' },
  { label: '内部人员', value: 'internal' },
  { label: '现场运维', value: 'ops' },
  { label: '厂商联系人', value: 'vendor_contact' },
]

const personTypeLabelMap = Object.fromEntries(personTypeOptions.map((item) => [item.value, item.label]))

export function personTypeLabel(value) {
  return personTypeLabelMap[value] || value || '-'
}
