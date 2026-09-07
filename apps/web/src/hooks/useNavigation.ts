import { useMemo } from "react"

import { useHasClinicalScope, useIsPlatformAdmin } from "@/hooks/useCanWrite"
import {
  isItemEnabled,
  MAIN_ITEMS,
  type NavItem,
  navPrefixes,
  SETTINGS_ITEMS,
  TOP_ITEMS,
} from "@/lib/navigation"

export interface EnabledNav {
  top: NavItem[]
  main: NavItem[]
  settings: NavItem[]
  /** Top, main and settings in one list, for search. */
  all: NavItem[]
  /** Every path the enabled items claim, for active-state resolution. */
  prefixes: string[]
}

/**
 * The nav items this session may see, with the same flag, platform-admin and
 * clinical-scope gates the sidebar applies. The sidebar and the search dialog
 * share it so a hidden module cannot reappear as a search result.
 */
export function useEnabledNavItems(): EnabledNav {
  const { isPlatformAdmin } = useIsPlatformAdmin()
  const { hasScope: hasClinicalScope } = useHasClinicalScope()

  return useMemo(() => {
    const allow = (item: NavItem) => isItemEnabled(item, isPlatformAdmin, hasClinicalScope)
    const top = TOP_ITEMS.filter(allow)
    const main = MAIN_ITEMS.filter(allow)
    const settings = SETTINGS_ITEMS.filter(allow)
    const all = [...top, ...main, ...settings]
    return { top, main, settings, all, prefixes: navPrefixes(all) }
  }, [isPlatformAdmin, hasClinicalScope])
}
