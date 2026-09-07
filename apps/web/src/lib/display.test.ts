import { describe, expect, it } from "vitest"

import { accountDisplayName, toProperCase } from "@/lib/display"

describe("toProperCase", () => {
  it("title-cases a stored name however it was entered", () => {
    expect(toProperCase("MINET UGANDA")).toBe("Minet Uganda")
    expect(toProperCase("acme")).toBe("Acme")
  })
})

describe("accountDisplayName", () => {
  it("prefers the account's own display name", () => {
    expect(accountDisplayName("Asha Kagwa", "a.k@example.com")).toBe("Asha Kagwa")
  })

  it("trims a padded display name", () => {
    expect(accountDisplayName("  Asha Kagwa  ", null)).toBe("Asha Kagwa")
  })

  it("builds a name from the email when there is no display name", () => {
    expect(accountDisplayName(null, "asha.kagwa@example.com")).toBe("Asha Kagwa")
    expect(accountDisplayName(null, "asha_kagwa@example.com")).toBe("Asha Kagwa")
    expect(accountDisplayName(null, "asha-kagwa@example.com")).toBe("Asha Kagwa")
  })

  it("never returns a raw email address", () => {
    for (const email of ["a.b@x.com", "admin@example.com", "x+tag@y.org"]) {
      expect(accountDisplayName(null, email)).not.toContain("@")
    }
  })

  it("drops numeric-only fragments rather than showing them as a name", () => {
    expect(accountDisplayName(null, "asha.123@example.com")).toBe("Asha")
  })

  it("returns null when there is nothing to build from", () => {
    expect(accountDisplayName(null, null)).toBeNull()
    expect(accountDisplayName("   ", "")).toBeNull()
    expect(accountDisplayName(null, "123@example.com")).toBeNull()
  })
})
