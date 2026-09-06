import { describe, expect, it } from "vitest"

import type { Contract } from "@/types/entities"

import { termLabel, termTone } from "./contract-term"

function contract(overrides: Partial<Contract>): Contract {
  return {
    is_active: true,
    is_auto_renew: false,
    days_remaining: 90,
    ...overrides,
  } as Contract
}

describe("termLabel", () => {
  it("distinguishes a renewal from an expiry", () => {
    expect(termLabel(contract({ is_auto_renew: true, days_remaining: 10 }))).toBe(
      "Renews in 10 days",
    )
    expect(termLabel(contract({ is_auto_renew: false, days_remaining: 10 }))).toBe(
      "Ends in 10 days",
    )
  })

  it("reads naturally at the day boundaries", () => {
    expect(termLabel(contract({ days_remaining: 1 }))).toBe("Ends tomorrow")
    expect(termLabel(contract({ days_remaining: 0 }))).toBe("Ends today")
  })

  it("reports an inactive term as ended regardless of the day count", () => {
    expect(termLabel(contract({ is_active: false, days_remaining: 5 }))).toBe("Ended")
  })
})

describe("termTone", () => {
  it("warns only when an expiry is near and nothing will renew it", () => {
    expect(termTone(contract({ is_auto_renew: false, days_remaining: 30 }))).toBe("text-warning")
    expect(termTone(contract({ is_auto_renew: true, days_remaining: 30 }))).toBe("text-fg-muted")
    expect(termTone(contract({ is_auto_renew: false, days_remaining: 31 }))).toBe("text-fg-muted")
  })

  it("flags an already-ended term as a problem", () => {
    expect(termTone(contract({ is_active: false }))).toBe("text-danger")
  })
})
