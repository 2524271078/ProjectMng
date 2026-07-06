export function buildMenuCodeSet(menus = []) {
  return new Set(
    (menus || [])
      .map((item) => item?.code)
      .filter(Boolean),
  )
}

export function hasMenuAccess(context = {}, code) {
  if (!code) return true
  if (context.isSuperuser) return true
  return (context.menuCodes || new Set()).has(code)
}

export function hasActionAccess(context = {}, menuCode, action = 'view') {
  if (!menuCode) return true
  if (context.isSuperuser) return true
  return (context.permissions || []).some((item) => item?.[0] === menuCode && item?.[1] === action)
}