export const PROJECT_STAGE_LABELS = {
  new: '立项',
  signed: '签约',
  delivery: '交付',
  ops: '运维',
}

export function projectStageLabel(value) {
  return PROJECT_STAGE_LABELS[value] || value || '-'
}
