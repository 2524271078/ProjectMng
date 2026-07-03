import { reactive } from 'vue'

export function buildPaginationState() {
  return reactive({
    page: 1,
    pageSize: 10,
    total: 0,
    totalPages: 1,
    rows: [],
    loading: false,
  })
}

export function applyPaginationResponse(state, payload = {}) {
  state.page = Number(payload.page || 1)
  state.pageSize = Number(payload.page_size || 10)
  state.total = Number(payload.count || 0)
  state.totalPages = Number(payload.total_pages || 1)
  state.rows = Array.isArray(payload.results) ? payload.results : []
  return state
}
