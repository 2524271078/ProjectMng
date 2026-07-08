export function validateCatalogForm(type, form) {
  if (type === 'line') {
    if (!form.name?.trim() || !form.code?.trim()) return '请填写产线名称和产线编码'
  }
  if (type === 'product') {
    if (!form.product_line) return '请先选择所属产线'
    if (!form.name?.trim()) return '请填写产品名称'
  }
  if (type === 'version') {
    if (!form.product) return '请先选择所属产品'
    if (!form.version_name?.trim()) return '请填写版本名称'
  }
  if (type === 'model') {
    if (!form.product) return '请先选择所属产品'
    if (!form.model_name?.trim()) return '请填写型号名称'
  }
  return ''
}
