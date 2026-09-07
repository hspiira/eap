import { describe, expect, it } from "vitest"

import { fixtureDashboard } from "@/api/endpoints/dashboard-fixture"
import { formatDelta, formatKpi, monthLabel, monthLabelLong, niceTicks } from "@/lib/dashboard"

describe("formatDelta", () => {
  it("reports growth against the prior period", () => {
    expect(formatDelta(60, 40)).toEqual({ label: "50%", direction: "up", tone: "success" })
  })

  it("reports decline", () => {
    expect(formatDelta(30, 40)).toEqual({ label: "25%", direction: "down", tone: "danger" })
  })

  it("stays silent when the prior period is empty or unchanged", () => {
    expect(formatDelta(10, 0)).toBeNull()
    expect(formatDelta(10, 10)).toBeNull()
    expect(formatDelta(400, 401)).toBeNull()
  })
})

describe("month labels", () => {
  it("renders short and long forms", () => {
    expect(monthLabel("2026-09")).toBe("Sep")
    expect(monthLabelLong("2026-01")).toBe("Jan 2026")
  })

  it("falls back to the raw key on malformed input", () => {
    expect(monthLabel("garbage")).toBe("garbage")
  })
})

describe("niceTicks", () => {
  it("ends above the maximum so bars keep headroom", () => {
    for (const max of [1, 7, 17, 20, 33, 7103]) {
      const ticks = niceTicks(max)
      expect(ticks[0]).toBe(0)
      expect(ticks[ticks.length - 1]).toBeGreaterThan(max)
      const step = ticks[1] - ticks[0]
      for (let i = 1; i < ticks.length; i++) expect(ticks[i] - ticks[i - 1]).toBe(step)
    }
  })

  it("handles an empty series", () => {
    expect(niceTicks(0)).toEqual([0, 1])
  })
})

describe("formatKpi", () => {
  it("compacts thousands", () => {
    expect(formatKpi(null)).toBe("-")
    expect(formatKpi(41)).toBe("41")
    expect(formatKpi(7103)).toBe("7.1k")
    expect(formatKpi(33050)).toBe("33k")
  })
})

describe("dashboard fixture", () => {
  it("serves twelve months ending in the current month", () => {
    const months = fixtureDashboard().sessions_monthly
    expect(months).toHaveLength(12)
    const now = new Date()
    const key = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
    expect(months[months.length - 1].month).toBe(key)
    for (const m of months) expect(m.month).toMatch(/^\d{4}-\d{2}$/)
  })
})
