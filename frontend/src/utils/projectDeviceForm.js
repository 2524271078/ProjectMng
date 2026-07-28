import { parseProductModelTreeValue } from './productModelTree.js'

export function createDefaultProjectDeviceForm() {
  return {
    bind_mode: 'new',
    device: null,
    device_model: null,
    device_name: '',
    serial_number: '',
    deploy_location: '',
    device_project_type: '',
    management_address: '',
    hardware_code: '',
    software_version: '',
    rule_library_version: '',
    version_update_method: '',
    license_info_text: '',
    is_standard_product: true,
    nonstandard_name: '',
    is_under_warranty: false,
    supports_remote: false,
    service_type: 'new_install',
    service_start_date: '',
    service_end_date: '',
    offline_date: '',
    ops_person: null,
    screenshot_url: '',
    rack_install_date: '',
    remark: '',
  }
}

export function buildProjectDevicePayload(form, { customerOrgId, salesPersonId }) {
  return {
    name: form.device_name,
    serial_number: form.serial_number,
    device_model: parseProductModelTreeValue(form.device_model),
    customer_org: customerOrgId ?? null,
    sales_person: salesPersonId ?? null,
    nonstandard_name: form.is_standard_product === false ? (form.nonstandard_name?.trim() || '') : '',
  }
}

export function buildProjectDeviceBindingPayload(form) {
  return {
    quantity: 1,
    deploy_location: form.deploy_location,
    device_project_type: form.device_project_type,
    service_type: form.service_type,
    service_start_date: form.service_start_date || null,
    service_end_date: form.service_end_date || null,
    offline_date: form.offline_date || null,
  }
}

export function validateProjectDeviceForm(form) {
  if (form.bind_mode === 'existing' && !form.device) return '请选择已有设备'

  if (form.bind_mode !== 'existing') {
    if (!parseProductModelTreeValue(form.device_model)) return '请选择设备名称'
    if (!form.device_name?.trim()) return '请填写产品型号'
    if (!form.serial_number?.trim()) return '请填写设备序列号'
  }

  if (!form.service_start_date) return '请选择服务开始日期'
  if (!form.service_end_date) return '请选择服务结束日期'
  if (form.service_end_date < form.service_start_date) return '服务结束日期不能早于开始日期'
  if (form.service_type === 'offline' && !form.offline_date) return '请选择下架时间'
  if (form.is_standard_product === false && !form.nonstandard_name?.trim()) return '请填写非标名称'
  return ''
}
