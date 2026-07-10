/**
 * Read/write a `tab` search parameter so the active tab survives reload + back navigation.
 *
 * Usage:
 *
 *   type TabValue = "overview" | "billing"
 *   const TABS = ["overview", "billing"] as const
 *   const [tab, setTab] = useTabSearchParam<TabValue>(TABS, "overview")
 *
 * Default tab is omitted from the URL to keep clean shareable links.
 */

import { useNavigate, useSearch } from '@tanstack/react-router'

interface SearchWithTab {
  tab?: string
}

export function useTabSearchParam<T extends string>(
  validValues: ReadonlyArray<T>,
  defaultValue: T,
): [T, (next: T) => void] {
  // Detail routes don't all declare a validateSearch, so read non-strictly.
  const search = useSearch({ strict: false }) as SearchWithTab
  const navigate = useNavigate()

  const fromUrl = search.tab && validValues.includes(search.tab as T) ? (search.tab as T) : null
  const tab: T = fromUrl ?? defaultValue

  const setTab = (next: T) => {
    navigate({
      search: ((prev: Record<string, unknown>) => ({
        ...prev,
        tab: next === defaultValue ? undefined : next,
      })) as never,
      replace: true,
    })
  }

  return [tab, setTab]
}
