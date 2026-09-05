import { describe, expect, it } from "vitest"

import { toLocalDateKey } from "@/lib/format"

describe("toLocalDateKey", () => {
  it("renders a Date as its local calendar day", () => {
    expect(toLocalDateKey(new Date(2026, 8, 4))).toBe("2026-09-04")
  })

  it("pads single-digit months and days", () => {
    expect(toLocalDateKey(new Date(2026, 0, 7))).toBe("2026-01-07")
  })

  it("returns a date-only string unchanged, in any timezone", () => {
    expect(toLocalDateKey("2026-09-04")).toBe("2026-09-04")
    expect(toLocalDateKey("  2026-01-07  ")).toBe("2026-01-07")
  })

  it("reads an instant in local time, not UTC", () => {
    const iso = "2026-09-04T00:00:00.000Z"
    const local = new Date(iso)
    const pad = (n: number) => String(n).padStart(2, "0")
    const expected = `${local.getFullYear()}-${pad(local.getMonth() + 1)}-${pad(local.getDate())}`
    expect(toLocalDateKey(iso)).toBe(expected)
  })

  it("agrees with itself when fed its own output", () => {
    const d = new Date(2026, 11, 31)
    expect(toLocalDateKey(toLocalDateKey(d))).toBe(toLocalDateKey(d))
  })

  it("returns an empty string for an unparseable value", () => {
    expect(toLocalDateKey("not a date")).toBe("")
  })
})
