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

export function projectStageLabel(value) {
  return PROJECT_STAGE_LABELS[value] || value || '-'
}

export function serviceTypeLabel(value) {
  return SERVICE_TYPE_LABELS[value] || value || '-'
}

export function signingSubjectLabel(value) {
  return SIGNING_SUBJECT_LABELS[value] || value || '-'
}
