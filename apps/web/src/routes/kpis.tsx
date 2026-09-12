import { createFileRoute } from "@tanstack/react-router"
import { BarChart3 } from "lucide-react"

import { AuthedLayout } from "@/components/common/AuthedLayout"
import { EmptyState } from "@/components/common/EmptyState"

export const Route = createFileRoute("/kpis")({
  component: KPIsRoute,
})

function KPIsRoute() {
  return (
    <AuthedLayout>
      <EmptyState
        icon={BarChart3}
        title="KPI dashboard coming soon"
        description="Real-time performance indicators and trend analytics across all modules. This module is in active development."
      />
    </AuthedLayout>
  )
}
