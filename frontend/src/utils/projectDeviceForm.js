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