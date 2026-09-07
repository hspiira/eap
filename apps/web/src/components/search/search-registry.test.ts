import { describe, expect, it } from "vitest"

import {
  countRecords,
  hasCategoryFailure,
  matchesActionQuery,
  RECORD_CATEGORIES,
  SEARCH_ACTIONS,
} from "@/components/search/search-registry"

/**
 * Every action must open a form that already exists. These routes and their
 * `?new=true` handoff are what `useListPage` reads; an action pointing
 * anywhere else would be a dead command in the palette.
 */
const VERIFIED_ENTRY_POINTS: Record<string, { to: string; opensCreateSheet: boolean }> = {
  "add-client": { to: "/clients", opensCreateSheet: true },
  "add-practitioner": { to: "/providers", opensCreateSheet: true },
  "add-provider-organisation": { to: "/provider-organisations", opensCreateSheet: true },
  "schedule-session": { to: "/service-sessions", opensCreateSheet: true },
}

describe("record categories", () => {
  it("covers exactly the first-release categories", () => {
    expect(RECORD_CATEGORIES.map((c) => c.key)).toEqual([
      "clients",
      "practitioners",
      "provider_organisations",
    ])
  })

  it("maps each type to a route rather than trusting the response", () => {
    expect(RECORD_CATEGORIES.map((c) => c.detailTo("x-1"))).toEqual([
      "/clients/x-1",
      "/providers/x-1",
      "/provider-organisations/x-1",
    ])
  })

  it("points See all at a list page that accepts a search query", () => {
    expect(RECORD_CATEGORIES.map((c) => c.listTo)).toEqual([
      "/clients",
      "/providers",
      "/provider-organisations",
    ])
  })

  it("gives every category its own failure wording", () => {
    const labels = RECORD_CATEGORIES.map((c) => c.failureLabel)
    expect(new Set(labels).size).toBe(labels.length)
  })
})

describe("actions", () => {
  it("names only verified entry points", () => {
    for (const action of SEARCH_ACTIONS) {
      const verified = VERIFIED_ENTRY_POINTS[action.id]
      expect(verified, `${action.id} has no verified entry point`).toBeDefined()
      expect(action.to).toBe(verified.to)
    }
  })

  it("opens a create sheet rather than carrying a mutation payload", () => {
    for (const action of SEARCH_ACTIONS) {
      expect(action.search).toEqual({ new: true })
    }
  })

  it("treats every action as a write, so Viewers do not see it", () => {
    for (const action of SEARCH_ACTIONS) {
      expect(action.requiresWrite).toBe(true)
    }
  })

  it("exposes no wellness nugget command", () => {
    // WELLNESS_NUGGETS_DECISION.md is not implemented; offering it would be a
    // command that does nothing.
    const text = JSON.stringify(SEARCH_ACTIONS)
    expect(/nugget/i.test(text)).toBe(false)
  })

  it("exposes no member action while member visibility is unreviewed", () => {
    expect(SEARCH_ACTIONS.some((a) => a.to.startsWith("/members"))).toBe(false)
  })

  it("finds an action by its aliases", () => {
    const book = SEARCH_ACTIONS.find((a) => a.id === "schedule-session")!
    expect(matchesActionQuery(book, "book session")).toBe(true)
    expect(matchesActionQuery(book, "appointment")).toBe(true)
    expect(matchesActionQuery(book, "invoice")).toBe(false)
  })
})

describe("response helpers", () => {
  const empty = { items: [], has_more: false, failed: false }

  it("counts records across every category", () => {
    expect(
      countRecords({
        clients: { ...empty, items: [{ id: "1", label: "A", secondary: null, type: "client" }] },
        practitioners: empty,
        provider_organisations: empty,
      }),
    ).toBe(1)
  })

  it("reports zero for a missing response rather than throwing", () => {
    expect(countRecords(undefined)).toBe(0)
    expect(hasCategoryFailure(undefined)).toBe(false)
  })

  it("detects a single failed category", () => {
    expect(
      hasCategoryFailure({
        clients: { ...empty, failed: true },
        practitioners: empty,
        provider_organisations: empty,
      }),
    ).toBe(true)
  })
})
