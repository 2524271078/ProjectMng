export function filterDevices(devices, { warrantyStatus = 'all', serviceType = 'all' } = {}) {
  return devices.filter((item) => {
    const matchesWarranty = warrantyStatus === 'all'
      || (warrantyStatus === 'in' ? item.current_service_status === '保内' : item.current_service_status !== '保内')

    const matchesServiceType = serviceType === 'all' || item.service_type === serviceType

    return matchesWarranty && matchesServiceType
  })
}
