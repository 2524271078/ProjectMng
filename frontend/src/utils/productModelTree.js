function createBranchNode(type, id, label, children = []) {
  return {
    key: `${type}-${id}`,
    type,
    id,
    label,
    disabled: true,
    children,
  }
}

function createModelNode(model) {
  return {
    key: `model-${model.id}`,
    type: 'model',
    id: model.id,
    label: model.model_name,
    disabled: false,
    children: [],
  }
}

export function buildProductModelTree({ lines = [], products = [], versions = [], models = [] }) {
  const modelsByVersion = new Map()
  const modelsByProduct = new Map()

  models.forEach((model) => {
    if (model.product_version) {
      if (!modelsByVersion.has(model.product_version)) modelsByVersion.set(model.product_version, [])
      modelsByVersion.get(model.product_version).push(model)
      return
    }
    if (!modelsByProduct.has(model.product)) modelsByProduct.set(model.product, [])
    modelsByProduct.get(model.product).push(model)
  })

  const versionsByProduct = new Map()
  versions.forEach((version) => {
    if (!versionsByProduct.has(version.product)) versionsByProduct.set(version.product, [])
    versionsByProduct.get(version.product).push(version)
  })

  const productsByLine = new Map()
  products.forEach((product) => {
    const lineKey = product.product_line ?? '__root__'
    if (!productsByLine.has(lineKey)) productsByLine.set(lineKey, [])
    productsByLine.get(lineKey).push(product)
  })

  function buildVersionNode(version) {
    return createBranchNode(
      'version',
      version.id,
      version.version_name,
      (modelsByVersion.get(version.id) || []).map(createModelNode),
    )
  }

  function buildProductNode(product) {
    const versionChildren = (versionsByProduct.get(product.id) || []).map(buildVersionNode)
    const directModels = (modelsByProduct.get(product.id) || []).map(createModelNode)
    return createBranchNode('product', product.id, product.name, [...versionChildren, ...directModels])
  }

  const lineNodes = lines.map((line) => createBranchNode('line', line.id, line.name, (productsByLine.get(line.id) || []).map(buildProductNode)))
  const rootProducts = (productsByLine.get('__root__') || []).map(buildProductNode)
  return [...lineNodes, ...rootProducts]
}
