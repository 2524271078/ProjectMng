import { apiClient } from './client'

export function listResource(resource, params = {}) {
  return apiClient.get(`/${resource}/`, { params })
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
