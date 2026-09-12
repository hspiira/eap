/**
 * Read/write a `tab` search parameter so the active tab survives reload and
 * takes its own place in history.
 *
 * Usage:
 *
 *   type TabValue = "overview" | "billing"
 *   const TABS = ["overview", "billing"] as const
 *   const [tab, setTab] = useTabSearchParam<TabValue>(TABS, "overview")
 *
 * Default tab is omitted from the URL to keep clean shareable links.
 *
 * Opening a tab pushes an entry, so back walks the tabs the user actually
 * visited before it leaves the page. Replacing the entry instead collapsed a
 * whole detail page into one entry, which is why back used to jump straight
 * out to the list from wherever the user had got to.
 */

import { useNavigate, useSearch } from "@tanstack/react-router"

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
    // Re-selecting the open tab would otherwise stack a duplicate entry that
    // back has to step through without anything on screen changing.
    if (next === tab) return
    navigate({
      search: ((prev: Record<string, unknown>) => ({
        ...prev,
        tab: next === defaultValue ? undefined : next,
      })) as never,
    })
  }

  return [tab, setTab]
}
