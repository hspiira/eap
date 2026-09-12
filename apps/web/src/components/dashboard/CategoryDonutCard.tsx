/** Sessions by category, on the shared breakdown donut. */

import type { CategoryCount } from "@/api/generated"

import { DonutBreakdownCard } from "./DonutBreakdownCard"

interface CategoryDonutCardProps {
  categories: ReadonlyArray<CategoryCount>
  insight?: string | null
  loading?: boolean
  error?: boolean
  onRetry?: () => void
}

export function CategoryDonutCard({
  categories,
  insight,
  loading,
  error,
  onRetry,
}: CategoryDonutCardProps) {
  return (
    <DonutBreakdownCard
      title="By category"
      slices={categories.map((c) => ({ key: c.category, label: c.category, total: c.total }))}
      centreNoun="sessions"
      emptyTitle="No categorised sessions"
      emptyDescription="A breakdown will appear here once sessions are logged in this window."
      insight={insight}
      loading={loading}
      error={error}
      onRetry={onRetry}
    />
  )
}
