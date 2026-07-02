export function buildPersonPayload(form, isEditing = false) {
  const payload = { ...form }
  if (!payload.organization) {
    if (isEditing) {
      payload.organization = null
    } else {
      delete payload.organization
    }
  }
  return payload
}
