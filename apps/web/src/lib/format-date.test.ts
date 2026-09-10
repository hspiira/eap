import { describe, expect, it } from "vitest"

import { formatDate, formatDateTime } from "@/lib/format"

describe("formatDate", () => {
  it("renders dd/mm/yyyy regardless of the viewer's own browser locale", () => {
    // Built from local parts, not a "Z" instant, so the assertion holds no
    // matter which timezone the test runs in.
    expect(formatDate(new Date(2026, 6, 14))).toBe("14/07/2026")
  })

  it("returns the placeholder for nothing usable", () => {
    expect(formatDate(null)).toBe("-")
    expect(formatDate(undefined)).toBe("-")
    expect(formatDate("")).toBe("-")
    expect(formatDate("nope")).toBe("-")
  })
})

describe("formatDateTime", () => {
  it("renders dd/mm/yyyy with a 24-hour time", () => {
    expect(formatDateTime(new Date(2026, 6, 14, 13, 45, 0))).toBe("14/07/2026 13:45:00")
  })

  it("returns the placeholder for nothing usable", () => {
    expect(formatDateTime(null)).toBe("-")
    expect(formatDateTime("nope")).toBe("-")
  })
})
