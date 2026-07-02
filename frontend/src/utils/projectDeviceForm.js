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
    is_under_warranty: false,
    supports_remote: false,
    ops_person: null,
    screenshot_url: '',
    rack_install_date: '',
    remark: '',
  }
}
