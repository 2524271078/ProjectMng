import { apiClient } from './client'

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

export function createProjectContract(payload) {
  return createResource('project-contracts', payload)
}

export function deleteProjectContract(id) {
  return deleteResource('project-contracts', id)
}

export function uploadAttachment(payload) {
  return apiClient.post('/attachments/upload/', payload, { headers: { 'Content-Type': 'multipart/form-data' } })
}
