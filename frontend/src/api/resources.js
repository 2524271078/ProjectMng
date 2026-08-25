import { apiClient } from './client'

function fetchDetailList(resource, id, detail, params = {}) {
  return apiClient.get(`/${resource}/${id}/${detail}/`, { params })
}

export function listResource(resource, params = {}) {
  return apiClient.get(`/${resource}/`, { params })
}

export async function listAllResource(resource, params = {}) {
  const firstResponse = await listResource(resource, params)
  const firstData = firstResponse.data

  if (!firstData || Array.isArray(firstData) || !Array.isArray(firstData.results)) {
    return firstResponse
  }

  const totalPages = Number(firstData.total_pages || 1)
  if (totalPages <= 1) {
    return firstResponse
  }

  const results = [...firstData.results]
  for (let page = 2; page <= totalPages; page += 1) {
    const { data } = await listResource(resource, { ...params, page })
    results.push(...(data.results || []))
  }

  return {
    ...firstResponse,
    data: {
      ...firstData,
      page: 1,
      page_size: results.length,
      total_pages: 1,
      count: results.length,
      results,
    },
  }
}

export function createResource(resource, payload) {
  return apiClient.post(`/${resource}/`, payload)
}

export function fetchDashboardReminders() {
  return apiClient.get('/dashboard-reminders/')
}

export function fetchDashboardOverview() {
  return apiClient.get('/dashboard-overview/')
}

export function confirmDashboardReminder(reminderKey) {
  return apiClient.post('/dashboard-reminders/confirm/', { reminder_key: reminderKey })
}

export function fetchCustomerOverview(id) {
  return apiClient.get(`/customers/${id}/overview/`)
}

export function fetchDeviceOverview(id) {
  return apiClient.get(`/devices/${id}/overview/`)
}

export function fetchContractOverview(id) {
  return apiClient.get(`/contracts/${id}/overview/`)
}

export function fetchSalesCustomers(id) {
  return apiClient.get(`/sales/${id}/customers/`)
}

export function updateResource(resource, id, payload) {
  return apiClient.patch(`/${resource}/${id}/`, payload)
}

export function deleteResource(resource, id) {
  return apiClient.delete(`/${resource}/${id}/`)
}

export function fetchSalesCustomerRelations(id) {
  return apiClient.get(`/sales/${id}/customer-relations/`)
}

export function saveSalesCustomerRelations(id, customerIds) {
  return apiClient.post(`/sales/${id}/customer-relations/`, { customer_ids: customerIds })
}

export function fetchProjectOverview(id) {
  return apiClient.get(`/projects/${id}/overview/`)
}

export function fetchCustomerDevices(id, params = {}) {
  return fetchDetailList('organizations', id, 'devices', params)
}

export function fetchCustomerProjects(id, params = {}) {
  return fetchDetailList('organizations', id, 'projects', params)
}

export function fetchCustomerContracts(id, params = {}) {
  return fetchDetailList('organizations', id, 'contracts', params)
}

export function fetchCustomerContacts(id, params = {}) {
  return fetchDetailList('organizations', id, 'contacts', params)
}

export function fetchCustomerSales(id, params = {}) {
  return fetchDetailList('organizations', id, 'sales', params)
}

export function createCustomerContact(id, payload) {
  return apiClient.post(`/organizations/${id}/contacts/`, payload)
}

export function deleteCustomerContact(id, personId) {
  return apiClient.delete(`/organizations/${id}/contacts/${personId}/`)
}

export function createCustomerSales(id, payload) {
  return apiClient.post(`/organizations/${id}/sales/`, payload)
}

export function deleteCustomerSales(id, personId) {
  return apiClient.delete(`/organizations/${id}/sales/${personId}/`)
}

export function fetchProjectDevices(id, params = {}) {
  return fetchDetailList('projects', id, 'devices', params)
}

export function fetchProjectContracts(id, params = {}) {
  return fetchDetailList('projects', id, 'contracts', params)
}

export function fetchProjectAttachments(id, params = {}) {
  return fetchDetailList('projects', id, 'attachments', params)
}

export function createProjectContract(payload) {
  return createResource('project-contracts', payload)
}

export function deleteProjectContract(id) {
  return deleteResource('project-contracts', id)
}

export function uploadAttachment(payload) {
  return apiClient.post('/attachments/upload/', payload, { headers: { 'Content-Type': 'multipart/form-data' } })
}
