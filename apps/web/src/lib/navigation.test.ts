import { describe, expect, it } from "vitest"

import {
  isItemEnabled,
  MAIN_ITEMS,
  matchesNavQuery,
  type NavItem,
  navPrefixes,
  resolveActive,
  SETTINGS_ITEMS,
  TOP_ITEMS,
} from "@/lib/navigation"

const ALL = [...TOP_ITEMS, ...MAIN_ITEMS, ...SETTINGS_ITEMS]
const PREFIXES = navPrefixes(ALL)

function item(label: string): NavItem {
  const found = ALL.find((i) => i.label === label)
  if (!found) throw new Error(`no nav item labelled ${label}`)
  return found
}

describe("one registry for the sidebar and search", () => {
  it("gives every item a label and a route", () => {
    for (const nav of ALL) {
      expect(nav.label.trim()).not.toBe("")
      expect(nav.to.startsWith("/")).toBe(true)
    }
  })

  it("has no duplicate labels, which would render twice in search", () => {
    const labels = ALL.map((i) => i.label)
    expect(new Set(labels).size).toBe(labels.length)
  })

  it("has no duplicate routes", () => {
    const routes = ALL.map((i) => i.to)
    expect(new Set(routes).size).toBe(routes.length)
  })

  it("keeps Providers as one entry owning both route families", () => {
    // docs/migrations/PROVIDERS_MIGRATION.md navigation decision, 2026-09-07.
    expect(item("Providers").matchPrefixes).toEqual(["/providers", "/provider-organisations"])
    expect(ALL.some((i) => i.to === "/provider-organisations")).toBe(false)
  })
})

describe("permission and flag gates", () => {
  it("hides a platform-admin entry from an ordinary tenant", () => {
    expect(isItemEnabled(item("Tenants"), false, true)).toBe(false)
    expect(isItemEnabled(item("Tenants"), true, true)).toBe(true)
  })

  it("hides a clinical entry without the scope", () => {
    expect(isItemEnabled(item("Cases"), false, false)).toBe(false)
    expect(isItemEnabled(item("Cases"), false, true)).toBe(true)
  })
})

describe("active-state resolution", () => {
  it("marks Providers active on both route families", () => {
    expect(resolveActive("/providers", item("Providers"), PREFIXES)).toBe(true)
    expect(resolveActive("/provider-organisations", item("Providers"), PREFIXES)).toBe(true)
    expect(resolveActive("/provider-organisations/org-1", item("Providers"), PREFIXES)).toBe(true)
  })

  it("does not mark Campaigns active while on the worklist", () => {
    expect(resolveActive("/care-callbacks/worklist", item("Campaigns"), PREFIXES)).toBe(false)
    expect(resolveActive("/care-callbacks/worklist", item("My Worklist"), PREFIXES)).toBe(true)
  })

  it("matches Home only exactly", () => {
    expect(resolveActive("/", item("Home"), PREFIXES)).toBe(true)
    expect(resolveActive("/clients", item("Home"), PREFIXES)).toBe(false)
  })
})

describe("search synonyms route to a destination", () => {
  it("finds Providers by practitioner and therapist", () => {
    for (const term of ["practitioner", "therapist", "counsellor"]) {
      expect(matchesNavQuery(item("Providers"), term)).toBe(true)
    }
  })

  it("finds Clients by employer", () => {
    expect(matchesNavQuery(item("Clients"), "employer")).toBe(true)
  })

  it("does not match an unrelated term", () => {
    expect(matchesNavQuery(item("Clients"), "practitioner")).toBe(false)
  })

  it("matches everything when nothing is typed", () => {
    expect(matchesNavQuery(item("Clients"), "")).toBe(true)
  })

  it("is case-insensitive on the label", () => {
    expect(matchesNavQuery(item("Clients"), "CLIENT")).toBe(true)
  })
})
