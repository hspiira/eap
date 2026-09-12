/**
 * The captions are arithmetic, so their claims are pinned as arithmetic.
 *
 * The rule under test throughout: a caption either says something the data
 * supports or it is null, never filler. These sentences sit directly under
 * charts, and a wrong sentence next to a right chart is worse than none.
 */

import { describe, expect, it } from "vitest"

import type { DashboardResponse } from "@/api/generated"
import {
  outcomeInsight,
  sessionsInsight,
  upcomingInsight,
  utilizationPerThousand,
  valueHint,
} from "@/lib/dashboard-insights"

function makeData(overrides: {
  sessions?: number
  sessions_prior?: number
  covered_members?: number
  sessions_unpriced?: number
  top_clients?: Array<{ client_id: string; client_name: string; total: number }>
}): DashboardResponse {
  return {
    kpis: {
      sessions: overrides.sessions ?? 0,
      sessions_prior: overrides.sessions_prior ?? 0,
      covered_members: overrides.covered_members ?? 0,
      sessions_unpriced: overrides.sessions_unpriced ?? 0,
      clients_served: 0,
      clients_with_roster: 0,
      clients_total: 0,
      import_backlog: 0,
      value_delivered_ugx: 0,
      contracts_ending_soon: 0,
    },
    top_clients: overrides.top_clients ?? [],
  } as DashboardResponse
}

describe("sessionsInsight", () => {
  it("names the movement and the dominant client", () => {
    const text = sessionsInsight(
      makeData({
        sessions: 100,
        sessions_prior: 80,
        top_clients: [{ client_id: "c1", client_name: "Minet Uganda", total: 38 }],
      }),
    )
    expect(text).toBe(
      "100 sessions, up 25% on the prior window; Minet Uganda accounts for 38% of delivery.",
    )
  })

  it("stays quiet about a client that does not dominate", () => {
    const text = sessionsInsight(
      makeData({
        sessions: 100,
        sessions_prior: 100,
        top_clients: [{ client_id: "c1", client_name: "Small Co", total: 10 }],
      }),
    )
    expect(text).toBe("100 sessions.")
  })

  it("does not invent a delta against an empty prior window", () => {
    expect(sessionsInsight(makeData({ sessions: 5 }))).toBe("5 sessions.")
  })

  it("says nothing about an empty window", () => {
    expect(sessionsInsight(makeData({}))).toBeNull()
  })
})

describe("outcomeInsight", () => {
  it("leads with the top recorded outcome and confesses the gap", () => {
    const text = outcomeInsight([
      { outcome: null, total: 186 },
      { outcome: "ToBeContinued", total: 124 },
      { outcome: "Completed", total: 59 },
    ])
    expect(text).toContain("leads the 183 recorded outcomes at 68%")
    expect(text).toContain("186 sessions are still unrecorded")
  })

  it("says plainly when nothing is recorded", () => {
    expect(outcomeInsight([{ outcome: null, total: 12 }])).toBe(
      "None of the 12 sessions in this window has an outcome recorded yet.",
    )
  })

  it("is null with no sessions at all", () => {
    expect(outcomeInsight([])).toBeNull()
  })
})

describe("upcomingInsight", () => {
  const day = (label: string, total: number) => ({ bucket: label, label, total })

  it("names the busiest day when bookings spread over several", () => {
    const text = upcomingInsight({
      total: 7,
      days: [day("Mon 01", 2), day("Tue 02", 5), day("Wed 03", 0)],
    })
    expect(text).toBe("7 bookings in the next 7 days, busiest Tue 02 with 5.")
  })

  it("collapses to the single day when there is only one", () => {
    const text = upcomingInsight({ total: 3, days: [day("Mon 01", 3), day("Tue 02", 0)] })
    expect(text).toBe("3 bookings in the next 7 days on Mon 01.")
  })

  it("is null for an empty week", () => {
    expect(upcomingInsight({ total: 0, days: [day("Mon 01", 0)] })).toBeNull()
  })
})

describe("utilizationPerThousand", () => {
  it("computes sessions per thousand covered members", () => {
    expect(utilizationPerThousand(makeData({ sessions: 90, covered_members: 3000 }))).toBe(30)
  })

  it("keeps one decimal, no more", () => {
    expect(utilizationPerThousand(makeData({ sessions: 1, covered_members: 3000 }))).toBe(0.3)
  })

  it("refuses to divide by nobody", () => {
    expect(utilizationPerThousand(makeData({ sessions: 5 }))).toBeNull()
  })
})

describe("valueHint", () => {
  it("counts the unpriced sessions the total silently excludes", () => {
    expect(valueHint(makeData({ sessions_unpriced: 3 }))).toBe("3 sessions unpriced")
  })

  it("is absent when every session carries a rate", () => {
    expect(valueHint(makeData({}))).toBeUndefined()
  })
})
