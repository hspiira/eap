import { describe, expect, it } from "vitest"

import { buildAttentionItems } from "@/components/dashboard/AttentionCard"
import { formatDelta, formatKpi, rangeLabel } from "@/lib/dashboard"
import { makeDashboard } from "@/test/dashboard"

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
  it("shows the whole figure, never a rounded 'k'", () => {
    expect(formatKpi(null)).toBe("-")
    expect(formatKpi(41)).toBe("41")
    expect(formatKpi(7103)).toBe("7,103")
    expect(formatKpi(33050)).toBe("33,050")
  })

  it("keeps two counts a rounded label would have collapsed together", () => {
    expect(formatKpi(2500)).not.toBe(formatKpi(3499))
  })
})

describe("rangeLabel", () => {
  it("names each preset", () => {
    expect(rangeLabel({ preset: "this_week" })).toBe("this week")
    expect(rangeLabel({ preset: "last_180d" })).toBe("last 6 months")
  })
})

describe("buildAttentionItems", () => {
  it("ranks blocking work above reporting gaps, and signals last", () => {
    const items = buildAttentionItems(makeDashboard())
    expect(items.map((i) => i.key)).toEqual([
      "practitioners",
      "rosters",
      "rates",
      "outcomes",
      "riser",
      "faller",
    ])
    expect(items[0].severity).toBe("high")
    expect(items[items.length - 1].severity).toBe("signal")
  })

  it("says nothing when every queue is clear and nothing has moved", () => {
    const data = makeDashboard({
      data_quality: {
        sessions_missing_outcome: 0,
        sessions_missing_rate: 0,
        clients_without_roster: 0,
        providers_pending: 0,
      },
      top_clients: [],
      trending_services: [],
    })
    expect(buildAttentionItems(data)).toEqual([])
  })

  it("raises a concentration signal only when one client dominates", () => {
    const spread = buildAttentionItems(makeDashboard())
    expect(spread.some((i) => i.key === "concentration")).toBe(false)

    const concentrated = buildAttentionItems(
      makeDashboard({
        top_clients: [{ client_id: "cl-1", client_name: "Stanbic Bank", total: 30 }],
      }),
    )
    const signal = concentrated.find((i) => i.key === "concentration")
    expect(signal?.headline).toBe("Stanbic Bank is 73% of delivery")
  })

  it("will not quote a percentage swing off a tiny prior window", () => {
    // 5 sessions against a prior window of 0 is not a trend, it is a first
    // occurrence, so no signal is raised from it.
    const items = buildAttentionItems(
      makeDashboard({
        trending_services: [
          {
            service_id: "sv-9",
            service_name: "New Service",
            total: 5,
            prior_total: 0,
            change_pct: null,
          },
          {
            service_id: "sv-8",
            service_name: "Barely Used",
            total: 4,
            prior_total: 2,
            change_pct: 100,
          },
        ],
      }),
    )
    expect(items.some((i) => i.key === "riser")).toBe(false)
  })

  it("stays quiet on a window too small to read anything into", () => {
    const items = buildAttentionItems(
      makeDashboard({
        kpis: { ...makeDashboard().kpis, sessions: 4 },
      }),
    )
    expect(items.some((i) => i.severity === "signal")).toBe(false)
  })
})
