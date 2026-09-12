/**
 * The sentence under each chart, written by arithmetic rather than a model.
 *
 * Every insight is a pure function of the aggregate the chart already shows,
 * so the caption can never disagree with the picture above it, costs nothing,
 * and is testable. A function returns null when the honest sentence would be
 * empty filler, and the card then shows no caption at all.
 */

import type { DashboardResponse, OutcomeCount, UpcomingBookings } from "@/api/generated"
import { getStatusLabel } from "@/utils/statusColors"

const CONCENTRATION_MENTION = 25

function pct(part: number, whole: number): number {
  return Math.round((part / whole) * 100)
}

/**
 * How the window compares with the one before it, and who drove it.
 * "312 sessions, up 24% on the prior window; Minet Uganda accounts for 38%."
 */
export function sessionsInsight(data: DashboardResponse): string | null {
  const { sessions, sessions_prior } = data.kpis
  if (sessions === 0) return null

  const count = `${sessions.toLocaleString()} session${sessions === 1 ? "" : "s"}`
  let movement = ""
  if (sessions_prior > 0 && sessions !== sessions_prior) {
    const change = pct(sessions - sessions_prior, sessions_prior)
    if (change !== 0) {
      movement = `, ${change > 0 ? "up" : "down"} ${Math.abs(change)}% on the prior window`
    }
  }

  const leader = data.top_clients[0]
  const share = leader ? pct(leader.total, sessions) : 0
  const concentration =
    leader && share >= CONCENTRATION_MENTION
      ? `; ${leader.client_name} accounts for ${share}% of delivery`
      : ""

  return `${count}${movement}${concentration}.`
}

/**
 * What the recorded outcomes say, and how much is still unrecorded.
 * The unrecorded share leads once it is the bigger story.
 */
export function outcomeInsight(mix: ReadonlyArray<OutcomeCount>): string | null {
  const total = mix.reduce((sum, item) => sum + item.total, 0)
  if (total === 0) return null

  const unrecorded = mix.find((item) => item.outcome === null)?.total ?? 0
  const recorded = total - unrecorded

  if (recorded === 0) {
    return `None of the ${total.toLocaleString()} sessions in this window has an outcome recorded yet.`
  }

  const top = mix.filter((item) => item.outcome !== null)[0]
  const lead = top
    ? `${getStatusLabel(top.outcome as string)} leads the ${recorded.toLocaleString()} recorded outcome${recorded === 1 ? "" : "s"} at ${pct(top.total, recorded)}%`
    : ""
  const gap =
    unrecorded > 0
      ? `; ${unrecorded.toLocaleString()} session${unrecorded === 1 ? " is" : "s are"} still unrecorded`
      : ""
  return `${lead}${gap}.`
}

/** The week ahead, with its busiest day when there is one. */
export function upcomingInsight(upcoming: UpcomingBookings): string | null {
  if (upcoming.total === 0) return null
  const busiest = upcoming.days.reduce((a, b) => (b.total > a.total ? b : a))
  const spread =
    upcoming.days.filter((d) => d.total > 0).length > 1
      ? `, busiest ${busiest.label} with ${busiest.total}`
      : ` on ${busiest.label}`
  return `${upcoming.total.toLocaleString()} booking${upcoming.total === 1 ? "" : "s"} in the next 7 days${spread}.`
}

/**
 * Sessions per 1,000 covered members: the industry's utilization figure.
 * Null when there is nobody covered, because 0/0 is not a rate.
 */
export function utilizationPerThousand(data: DashboardResponse): number | null {
  const { sessions, covered_members } = data.kpis
  if (covered_members === 0) return null
  return Math.round((sessions / covered_members) * 1000 * 10) / 10
}

/** "UGX 12,400,000" with the honesty clause about unpriced sessions. */
export function valueHint(data: DashboardResponse): string | undefined {
  const unpriced = data.kpis.sessions_unpriced
  if (unpriced === 0) return undefined
  return `${unpriced.toLocaleString()} session${unpriced === 1 ? "" : "s"} unpriced`
}
