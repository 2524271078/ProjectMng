export function formatDeviceOptionLabel(device, deviceModels = []) {
  const parts = [device.name, device.serial_number].filter(Boolean)
  const model = deviceModels.find((item) => item.id === device.device_model)
  if (model?.model_name) parts.push(model.model_name)
  return parts.join(' / ')
}
