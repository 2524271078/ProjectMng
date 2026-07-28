export const PROJECT_STAGE_LABELS = {
  new: '立项',
  signed: '签约',
  delivery: '交付',
  ops: '运维',
}

export const SERVICE_TYPE_LABELS = {
  new_install: '新装',
  renewal: '续保',
  offline: '下架',
}

export const SIGNING_SUBJECT_LABELS = {
  direct: '直签',
  agent: '代理',
}

export const INSPECTION_TASK_STATUS_LABELS = {
  pending: '待巡检',
  completed: '已完成',
  overdue: '已逾期',
  cancelled: '已取消',
}

export const OPERATION_RECORD_TYPE_LABELS = {
  inspection: '巡检',
  system_upgrade: '系统升级',
  rule_library_upgrade: '规则库升级',
  fault_handling: '故障处理',
  configuration_change: '配置变更',
  technical_support: '技术支持',
  other: '其他',
}

export function projectStageLabel(value) {
  return PROJECT_STAGE_LABELS[value] || value || '-'
}

export function serviceTypeLabel(value) {
  return SERVICE_TYPE_LABELS[value] || value || '-'
}

export function signingSubjectLabel(value) {
  return SIGNING_SUBJECT_LABELS[value] || value || '-'
}

export function inspectionTaskStatusLabel(value) {
  return INSPECTION_TASK_STATUS_LABELS[value] || value || '-'
}

export function operationRecordTypeLabel(value) {
  return OPERATION_RECORD_TYPE_LABELS[value] || value || '-'
}
