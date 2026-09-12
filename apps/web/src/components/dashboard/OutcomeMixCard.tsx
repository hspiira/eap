/**
 * Clinical outcomes of the window's completed sessions.
 *
 * Rendered only when the API sent the block, which it does only for a caller
 * holding the clinical scope; the wall fails closed server-side and this card
 * simply is not there for anyone else. Sessions with no recorded outcome keep
 * their own muted slice, because an absent value is not an identity.
 */

import type { OutcomeCount } from "@/api/generated"
import { getStatusLabel } from "@/utils/statusColors"

import { DonutBreakdownCard, type DonutSlice } from "./DonutBreakdownCard"

interface OutcomeMixCardProps {
  mix: ReadonlyArray<OutcomeCount>
  insight?: string | null
  loading?: boolean
}

function toSlice(item: OutcomeCount): DonutSlice {
  if (item.outcome === null) {
    return {
      key: "not-recorded",
      label: "Not recorded",
      total: item.total,
      color: "var(--color-chart-muted)",
    }
  }
  return { key: item.outcome, label: getStatusLabel(item.outcome), total: item.total }
}

export function OutcomeMixCard({ mix, insight, loading }: OutcomeMixCardProps) {
  return (
    <DonutBreakdownCard
      title="Clinical outcomes"
      slices={mix.map(toSlice)}
      centreNoun="sessions"
      emptyTitle="No completed sessions"
      emptyDescription="Outcomes appear here once sessions complete in this window."
      insight={insight}
      loading={loading}
    />
  )
}
