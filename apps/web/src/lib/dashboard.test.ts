import { describe, expect, it } from "vitest"

import { fixtureDashboard } from "@/api/endpoints/dashboard-fixture"
import { buildAttentionItems } from "@/components/dashboard/AttentionCard"
import { formatDelta, formatKpi, rangeLabel } from "@/lib/dashboard"

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

describe("formatKpi", () => {
  it("compacts thousands", () => {
    expect(formatKpi(null)).toBe("-")
    expect(formatKpi(41)).toBe("41")
    expect(formatKpi(7103)).toBe("7.1k")
    expect(formatKpi(33050)).toBe("33k")
  })
})

describe("rangeLabel", () => {
  it("names each preset", () => {
    expect(rangeLabel({ preset: "this_week" })).toBe("this week")
    expect(rangeLabel({ preset: "last_180d" })).toBe("last 6 months")
  })
})

describe("dashboard fixture", () => {
  it("re-buckets with the requested window", () => {
    expect(fixtureDashboard({ preset: "this_week" }).range.granularity).toBe("day")
    expect(fixtureDashboard({ preset: "last_90d" }).range.granularity).toBe("week")
    expect(fixtureDashboard({ preset: "last_180d" }).range.granularity).toBe("month")
  })

  it("keeps the KPI total equal to the series it charts", () => {
    for (const preset of ["this_week", "last_30d", "last_90d", "last_180d"] as const) {
      const data = fixtureDashboard({ preset })
      const summed = data.sessions_series.reduce((total, point) => total + point.total, 0)
      expect(data.kpis.sessions).toBe(summed)
    }
  })

  it("splits every bucket into bands that add up to its total", () => {
    for (const point of fixtureDashboard({ preset: "last_30d" }).sessions_series) {
      expect(point.physical + point.online + point.unknown).toBe(point.total)
    }
  })
})

describe("buildAttentionItems", () => {
  it("ranks blocking work above reporting gaps", () => {
    const items = buildAttentionItems(fixtureDashboard({ preset: "last_90d" }))
    expect(items.map((i) => i.key)).toEqual(["practitioners", "rosters", "rates", "outcomes"])
    expect(items[0].severity).toBe("high")
    expect(items[items.length - 1].severity).toBe("low")
  })

  it("says nothing when every queue is clear", () => {
    const data = fixtureDashboard({ preset: "last_90d" })
    data.data_quality = {
      sessions_missing_outcome: 0,
      sessions_missing_rate: 0,
      clients_without_roster: 0,
      providers_pending: 0,
    }
    expect(buildAttentionItems(data)).toEqual([])
  })
})

describe("fixture groupings stay inside the window total", () => {
  it("never lets a subset outrun the whole", () => {
    for (const preset of ["this_week", "last_30d", "last_90d", "last_180d"] as const) {
      const data = fixtureDashboard({ preset })
      const sessions = data.kpis.sessions
      const sum = (values: number[]) => values.reduce((a, b) => a + b, 0)
      expect(sum(data.sessions_by_category.map((c) => c.total))).toBe(sessions)
      expect(sum(data.top_clients.map((c) => c.total))).toBeLessThanOrEqual(sessions)
      expect(sum(data.trending_services.map((s) => s.total))).toBeLessThanOrEqual(sessions)
    }
  })
})
