export function filterDevices(devices, { warrantyStatus = 'all', serviceType = 'all', signingSubject = 'all' } = {}) {
  return devices.filter((item) => {
    const matchesWarranty = warrantyStatus === 'all'
      || (warrantyStatus === 'in' ? item.current_service_status === '保内' : item.current_service_status !== '保内')

    const matchesServiceType = serviceType === 'all' || item.service_type === serviceType
    const matchesSigningSubject = signingSubject === 'all' || item.current_signing_subject === signingSubject

    return matchesWarranty && matchesServiceType && matchesSigningSubject
  })
}
