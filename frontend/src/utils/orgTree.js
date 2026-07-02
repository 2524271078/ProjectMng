export function buildOrganizationTree(organizations) {
  const nodeMap = new Map()
  const roots = []

  for (const organization of organizations) {
    nodeMap.set(organization.id, { ...organization, children: [] })
  }

  for (const organization of organizations) {
    const node = nodeMap.get(organization.id)
    const parentId = organization.parent
    const parent = parentId ? nodeMap.get(parentId) : null
    if (parent) {
      parent.children.push(node)
    } else {
      roots.push(node)
    }
  }

  return roots
}
