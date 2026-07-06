function sortActions(actions = []) {
  return [...new Set(actions)].sort()
}

export function groupPermissionPairsByMenu(permissionPairs = []) {
  return permissionPairs.reduce((accumulator, item) => {
    const [menuId, action] = item || []
    if (!menuId || !action) return accumulator
    const key = String(menuId)
    accumulator[key] = sortActions([...(accumulator[key] || []), action])
    return accumulator
  }, {})
}

export function buildPermissionRecordsDiff(existingRecords = [], selectedMap = {}) {
  const selectedEntries = Object.entries(selectedMap || {})
  const selectedKeys = new Set(
    selectedEntries.flatMap(([menuId, actions]) =>
      (actions || []).map((action) => `${menuId}:${action}`),
    ),
  )
  const existingKeys = new Set(existingRecords.map((item) => `${item.menu}:${item.action}`))

  const toCreate = selectedEntries.flatMap(([menuId, actions]) =>
    (actions || [])
      .filter((action) => !existingKeys.has(`${menuId}:${action}`))
      .map((action) => ({ menu: Number(menuId), action })),
  )

  const toDeleteIds = existingRecords
    .filter((item) => !selectedKeys.has(`${item.menu}:${item.action}`))
    .map((item) => item.id)
    .sort((left, right) => left - right)

  return { toCreate, toDeleteIds }
}